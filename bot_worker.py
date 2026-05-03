# bot_worker.py

import os
import time
import cv2
import adbutils
import datetime
import shutil
from PySide6.QtCore import QThread, Signal
from config import STAGE_DATA

class BotWorker(QThread):
    # 建立一個用來通知主介面工作結束的訊號
    finished_signal = Signal() 
    
    # 初始化函式，接收主介面傳來的分類、關卡與隊伍設定
    def __init__(self, category, stage, team_config):
        # 呼叫父類別的初始化函式
        super().__init__()
        # 將傳入的分類名稱存為類別變數
        self.category = category
        # 將傳入的關卡名稱存為類別變數
        self.stage = stage
        # 將傳入的隊伍設定(字典)存為類別變數
        self.team_config = team_config
        # 設定一個控制迴圈是否繼續執行的布林開關
        self.is_running = True 
        # 宣告一個變數用來存放 ADB 設備物件
        self.device = None

    # 初始化 ADB 連線的專屬方法
    def init_adb(self):
        try:
            # 強制 ADB 重新連接指定的 IP 與通訊埠
            adbutils.adb.connect("127.0.0.1:16384")
            # 將連線成功的設備物件存入類別變數 self.device
            self.device = adbutils.adb.device(serial="127.0.0.1:16384")
            return True
        except Exception as e:
            # 如果連線失敗，則回傳 False
            return False
        
    def write_log(self, message):
        # 取得現在的時間，格式為 YYYY-MM-DD HH:MM:SS
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 組合出要寫入的字串
        log_string = f"[{current_time}] {message}\n"
    
        # 將字串附加寫入到 logs/system.log 檔案中 (檔案不存在會自動建立)
        with open(os.path.join("logs", "system.log"), "a", encoding="utf-8") as f:
            f.write(log_string)


    # 聰明的睡眠機制：將長睡眠切碎，以便隨時響應停止指令
    def smart_sleep(self, duration):
        # 將傳入的秒數除以 0.1，計算出需要睡幾個 0.1 秒的片段
        intervals = int(duration / 0.1)
        # 迴圈執行對應的次數
        for _ in range(intervals):
            # 如果外部將 is_running 設為 False，立刻打破迴圈醒來
            if not self.is_running:
                break
            # 睡 0.1 秒
            time.sleep(0.1)
        # 處理無法被 0.1 整除的剩餘小數點時間
        if self.is_running and (duration % 0.1) > 0:
            time.sleep(duration % 0.1)

    # 確認目標圖片是否存在於目前畫面上
    def check_exists(self, target_image_name):
        # 如果設備未連線或已經收到停止指令，直接回傳 False
        if self.device is None or not self.is_running: return False
        
        # 讓模擬器截圖並存檔為 screen.png
        self.device.screenshot().save("screen.png")
        # 讀取剛剛截下來的畫面
        img_screen = cv2.imread("screen.png")
        # 組合出目標小圖的完整路徑
        image_path = os.path.join("images", target_image_name)
        # 讀取目標小圖
        img_target = cv2.imread(image_path)
        
        # 防呆機制：如果找不到目標小圖的檔案，回傳 False
        if img_target is None: return False
        
        # 進行特徵比對，計算兩張圖的相似度
        result = cv2.matchTemplate(img_screen, img_target, cv2.TM_CCOEFF_NORMED)
        # 取得比對結果的最大值(最高相似度)等數據
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        # 如果最高相似度大於 0.9 (90%)，代表找到圖片，回傳 True
        if max_val > 0.9: return True
        return False

    # 確認圖片存在並點擊它
    def smart_click(self, target_image_name):
        # 如果設備未連線或已經收到停止指令，直接回傳 False
        if self.device is None or not self.is_running: return False
        
        # 讓模擬器截圖並存檔
        self.device.screenshot().save("screen.png")
        # 讀取畫面大圖
        img_screen = cv2.imread("screen.png")
        # 組合目標圖片路徑
        image_path = os.path.join("images", target_image_name)
        # 讀取目標小圖
        img_target = cv2.imread(image_path)
        
        # 防呆機制：確保圖案存在
        if img_target is None: return False
        
        # 進行特徵比對
        result = cv2.matchTemplate(img_screen, img_target, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        # 如果相似度達標
        if max_val > 0.9:
            # 取得目標圖片的高度與寬度
            h, w = img_target.shape[:2]
            # 計算出圖片的中心 X 座標
            center_x = max_loc[0] + w // 2
            # 計算出圖片的中心 Y 座標
            center_y = max_loc[1] + h // 2
            
            # 透過 ADB 指令點擊計算出的中心座標
            self.device.click(center_x, center_y)
            # 呼叫微秒睡眠，等待遊戲畫面反應 (1秒)
            self.smart_sleep(1.0)
            return True
        return False

    # 執行緒啟動後會自動執行此函式
    def run(self):
        # 嘗試初始化 ADB，若失敗則印出警告並結束任務
        if not self.init_adb():
            print("[警告] ADB 連線失敗，無法執行任務，請確認模擬器狀態。")
            self.finished_signal.emit()
            return

        # 根據傳入的分類與關卡，從資料庫轉換出需要尋找的看板圖片檔名
        self.target_banner = STAGE_DATA[self.category][self.stage]["banner"]
        # 根據傳入的分類與關卡，從資料庫轉換出需要尋找的關卡圖片檔名
        self.target_stage = STAGE_DATA[self.category][self.stage]["stage"]
    
        # 印出啟動提示與目標
        print("[系統] 啟動自動化任務...")
        print(f"[目標] 看板: {self.category} | 關卡: {self.stage}")
        # 初始化迷失計數器
        unknown_count = 0
         
        # 當布林開關為 True 時，不斷重複執行此迴圈
        while self.is_running:
            # 印出分隔線以利閱讀
            print("-" * 30)

            # 檢查首頁按鈕
            if self.check_exists("task.png"):
                unknown_count = 0
                print("[狀態] 目前在首頁，準備進入任務選單...")
                self.smart_click("task.png")

            # 檢查目標看板
            elif self.check_exists(self.target_banner):
                unknown_count = 0
                print("[狀態] 看到目標看板，準備進入分類...")
                self.smart_click(self.target_banner)

            # 檢查關卡內部標題
            elif self.check_exists("title_training.png"):
                unknown_count = 0
                # 尋找目標關卡
                if self.check_exists(self.target_stage): 
                    print("[狀態] 找到目標關卡，準備點擊進入...")
                    self.smart_click(self.target_stage)
                else:
                    print("[狀態] 找不到目標關卡圖示，嘗試向下滑動...")
                    # 模擬手指滑動
                    self.device.swipe(1400, 800, 1400, 300, 0.5) 
                    # 呼叫微秒睡眠等待動畫
                    self.smart_sleep(1.5) 
            
            # 檢查進入戰鬥按鈕
            elif self.check_exists("btn_enter.png"): 
                unknown_count = 0
                print("[狀態] 在隊伍配置畫面")
                print(f"[預備] 已讀取隊伍配置：{self.team_config}")
                
                print("[執行] 嘗試倍率最大化...")
                # 迴圈 4 次點擊加號
                for _ in range(4):
                    if not self.is_running: break # 如果被停止則中斷迴圈
                    self.device.click(1860, 900)
                    self.smart_sleep(0.5)
                    
                attempts = 0
                # 最多嘗試 5 次進入戰鬥
                while attempts < 5 and self.is_running:
                    # 點擊進入
                    self.smart_click("btn_enter.png") 
                    self.smart_sleep(1.5) 
                    
                    # 檢查體力不足彈窗
                    if self.check_exists("popup_replenish.png"): 
                        print(f"[警告] 體力不足，觸發彈窗 (剩餘嘗試次數：{4 - attempts})")
                        self.smart_click("btn_cancel_replenish.png") 
                        self.smart_sleep(0.5)
                        # 點擊減號
                        self.device.click(1335, 900) 
                        self.smart_sleep(0.5)
                        attempts += 1 
                    else:
                        print("[系統] 成功進入戰鬥，脫離配置環節。")
                        break 

                # 若嘗試 5 次皆失敗，自動停止任務
                if attempts >= 5:
                    print("[系統] 體力不足，自動終止任務。")
                    self.is_running = False 
                    self.write_log(f"[INFO] 體力耗盡，任務結束 - 看板: {self.category}, 關卡: {self.stage}")
                    break 

            # 檢查戰鬥勝利結算畫面
            elif self.check_exists("battle_victory.png"):
                unknown_count = 0
                print("[狀態] 戰鬥勝利，點擊結算...")
                self.smart_click("battle_victory.png")
                self.write_log(f"[SUCCESS] 戰鬥勝利 - 看板: {self.category}, 關卡: {self.stage}")

            # 處理未知畫面防呆機制
            else:
                unknown_count += 1 
                print(f"[狀態] 未知畫面辨識中... (連續迷失 {unknown_count} 次)")
                if unknown_count >= 3:
                    print("[執行] 觸發看門狗喚醒機制：點擊安全區域")

                    # 🌟 新增：異常記錄與截圖存證
                    # 取得用來當檔名的時間戳記 (不能有冒號，所以用底線)
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    fail_image_name = f"fail_{timestamp}.png"
                    fail_image_path = os.path.join("logs", "fail_cases", fail_image_name)
                    
                    # 將當下的 screen.png 複製到 fail_cases 資料夾並重新命名
                    if os.path.exists("screen.png"):
                        shutil.copy("screen.png", fail_image_path)
                    
                    self.write_log(f"[WARNING] 觸發喚醒機制 - 已儲存異常截圖: {fail_image_name}")
                    # 🌟 新增結束

                    self.device.click(100, 500) 
                    self.smart_sleep(1.0)
                    unknown_count = 0
            
            # 單次大迴圈結束後，呼叫微秒睡眠 2 秒
            self.smart_sleep(2.0)
                
        # 任務結束，印出停止提示
        print("\n[系統] 腳本已停止運作。")
        # 發送訊號通知主介面解鎖按鈕
        self.finished_signal.emit()

    # 定義供外部呼叫的停止函式
    def stop(self):
        # 將開關關閉，使得 smart_sleep 與 main loop 立刻打破
        self.is_running = False