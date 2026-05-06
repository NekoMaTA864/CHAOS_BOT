# main_ui.py
import os
import sys
import json
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QComboBox, QPushButton, QTextEdit, QGridLayout)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QTextCursor

# 匯入其他模組中的常數與類別
from config import CONFIG_FILE, CHARACTERS, ARCHIVES, STAGE_DATA
from bot_worker import BotWorker

# 定義一個類別，負責攔截 Python 原本要印在終端機的文字
class StreamRedirector(QObject):
    # 建立一個字串型態的廣播訊號
    text_written = Signal(str)
    
    # 覆寫寫入方法，將文字當作訊號發射出去
    def write(self, text):
        self.text_written.emit(str(text))
        
    # 覆寫快取清理方法，留空即可
    def flush(self):
        pass

# 定義主視窗類別，繼承自 QMainWindow
class MainWindow(QMainWindow):
    # 初始化介面與各種元件
    def __init__(self):
        super().__init__()
        # 設定視窗標題
        self.setWindowTitle("Chaos Bot - System UI")
        # 設定視窗預設大小
        self.resize(480, 720) 
        
        # 呼叫自訂的函式，從外部檔案載入並套用樣式表
        self.load_stylesheet("style.qss")

        # 定義一個函式，專門用來讀取外部的 QSS 檔案並套用到主視窗
    def load_stylesheet(self, file_path):
        # 匯入作業系統模組，用來檢查檔案是否存在
        import os
        # 檢查指定的樣式表檔案是否存在於路徑中
        if os.path.exists(file_path):
            # 使用 with 語法安全地開啟檔案，確保讀取後會自動關閉檔案，並指定 utf-8 編碼以支援中文註解
            with open(file_path, "r", encoding="utf-8") as f:
                # 讀取檔案內的所有文字內容，並將其套用到目前的主視窗 (self) 上
                self.setStyleSheet(f.read())
        else:
            # 如果找不到檔案，在終端機印出警告訊息，讓開發者知道樣式載入失敗
            print(f"[警告] 找不到樣式表檔案：{file_path}，將使用系統預設介面。")
            
        # 呼叫讀取設定檔的函式，並存入字典
        self.config = self.load_config()

        # 建立中央畫布
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        # 設定垂直排列的佈局管理器
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(12)

        # 建立目標關卡選擇的文字標籤
        lbl_target = QLabel("目標關卡選擇")
        lbl_target.setStyleSheet("font-size: 16px; color: #85C9DC;") 
        layout.addWidget(lbl_target)

        # 建立一個水平排列的佈局，放兩個下拉選單
        combo_layout = QVBoxLayout()
        # 建立主分類選單
        self.combo_category = QComboBox()
        self.combo_category.addItems(list(STAGE_DATA.keys()))
        combo_layout.addWidget(self.combo_category)
        
        # 建立次分類(關卡)選單
        self.combo_stage = QComboBox()
        combo_layout.addWidget(self.combo_stage)
        layout.addLayout(combo_layout)

        # 當主分類改變時更新次分類
        self.combo_category.currentTextChanged.connect(self.update_stage_combo)
        
        # 讀取並套用記憶的關卡
        saved_category = self.config.get("target_category", "戰鬥員")
        self.combo_category.setCurrentText(saved_category)
        self.update_stage_combo(saved_category)
        self.combo_stage.setCurrentText(self.config.get("target_stage", ""))

        # 增加畫布間距並建立隊伍配置區
        layout.addSpacing(10)
        lbl_team = QLabel("出戰隊伍與存檔配置")
        lbl_team.setStyleSheet("font-size: 14px; color: #85C9DC;")
        layout.addWidget(lbl_team)

        # 建立網格佈局
        team_grid = QGridLayout()
        team_grid.setSpacing(10)
        
        # 建立陣列存放隊員選單
        self.team_combos = [] 
        for i in range(3):
            lbl_char = QLabel(f"隊員 {i+1} :")
            
            combo_char = QComboBox()
            combo_char.addItems(CHARACTERS)
            combo_char.setCurrentText(self.config.get(f"char_{i}", "無/不更改"))
            
            combo_arch = QComboBox()
            combo_arch.addItems(ARCHIVES)
            combo_arch.setCurrentText(self.config.get(f"arch_{i}", "不切換"))

            # 綁定改變事件到存檔函式
            combo_char.currentTextChanged.connect(self.save_config_state)
            combo_arch.currentTextChanged.connect(self.save_config_state)

            team_grid.addWidget(lbl_char, i, 0)
            team_grid.addWidget(combo_char, i, 1)
            team_grid.addWidget(combo_arch, i, 2)
            
            self.team_combos.append({"char": combo_char, "arch": combo_arch})
            
        layout.addLayout(team_grid)

        # 綁定分類改變事件到存檔函式
        self.combo_category.currentTextChanged.connect(self.save_config_state)
        self.combo_stage.currentTextChanged.connect(self.save_config_state)

        # 建立按鈕區域
        layout.addSpacing(15)
        btn_layout = QVBoxLayout()
        
        # 建立啟動按鈕
        self.btn_start = QPushButton("啟動自動化管線")
        self.btn_start.setObjectName("btn_start")
        btn_layout.addWidget(self.btn_start)

        # 建立停止按鈕，預設為不可點擊(觸發禁用樣式)
        self.btn_stop = QPushButton("強制停止")
        self.btn_stop.setObjectName("btn_stop")
        self.btn_stop.setEnabled(False) 
        btn_layout.addWidget(self.btn_stop)

        # 建立一個開啟日誌資料夾的按鈕
        self.btn_open_log = QPushButton("開啟 Log 紀錄資料夾")
        self.btn_open_log.setObjectName("btn_open_log")
        # 將按鈕加入介面佈局
        btn_layout.addWidget(self.btn_open_log)
        
        # 綁定點擊事件到開啟資料夾的函式
        self.btn_open_log.clicked.connect(self.open_log_folder)
        
        layout.addLayout(btn_layout)

        # 建立終端機區域
        layout.addSpacing(10)
        lbl_console = QLabel("系統執行日誌")
        lbl_console.setStyleSheet("font-size: 13px; color: #EEDA01;") 
        layout.addWidget(lbl_console)

        # 建立唯讀的文字輸出框
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True) 
        layout.addWidget(self.console_output)

        # 連接按鈕事件
        self.btn_start.clicked.connect(self.start_bot)
        self.btn_stop.clicked.connect(self.stop_bot)
        
        self.worker = None

        # 實例化文字攔截器並連接訊號
        self.redirector = StreamRedirector()
        self.redirector.text_written.connect(self.append_console_text)
        sys.stdout = self.redirector

        print("[系統] 介面載入完成，等待指令。")

    # 定義讀取 JSON 設定檔的函式
    def load_config(self):
        import os
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                pass
        return {}

    # 定義儲存 JSON 設定檔的函式
    def save_config_state(self):
        config_data = {
            "target_category": self.combo_category.currentText(),
            "target_stage": self.combo_stage.currentText()
        }
        for i, combos in enumerate(self.team_combos):
            config_data[f"char_{i}"] = combos["char"].currentText()
            config_data[f"arch_{i}"] = combos["arch"].currentText()
            
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)

    # 根據選擇的分類動態更新次分類
    def update_stage_combo(self, category_name):
        if not category_name: return
        self.combo_stage.clear()
        stages = list(STAGE_DATA[category_name].keys())
        self.combo_stage.addItems(stages)

    # 將文字輸出到介面的日誌框
    def append_console_text(self, text):
        cursor = self.console_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.console_output.setTextCursor(cursor)
        self.console_output.ensureCursorVisible() 

    # 處理啟動按鈕的邏輯
    def start_bot(self):
        self.save_config_state() 
        category = self.combo_category.currentText()
        stage = self.combo_stage.currentText()
        
        # 打包隊伍設定
        team_config = []
        for combos in self.team_combos:
            team_config.append({
                "char": combos["char"].currentText(),
                "arch": combos["arch"].currentText()
            })
        
        # 實例化背景工人
        self.worker = BotWorker(category, stage, team_config)
        # 綁定結束訊號，以便恢復 UI
        self.worker.finished_signal.connect(self.reset_ui)
        # 啟動工人執行緒
        self.worker.start() 
        
        # 啟動後，將啟動按鈕設為禁用，解鎖停止按鈕
        self.btn_start.setEnabled(False)
        self.combo_category.setEnabled(False) 
        self.combo_stage.setEnabled(False)
        self.btn_stop.setEnabled(True)
        # 鎖定隊伍選單
        for combos in self.team_combos:
            combos["char"].setEnabled(False)
            combos["arch"].setEnabled(False)

    # 處理停止按鈕的邏輯
    def stop_bot(self):
        if self.worker and self.worker.isRunning():
            print("[系統] 收到停止指令，正在立即中斷執行緒...")
            # 呼叫工人的停止方法，其內部的 smart_sleep 會立刻跳出
            self.worker.stop()
            # 點擊後立刻禁用停止按鈕，防止連續點擊
            self.btn_stop.setEnabled(False)

    # 在 MainWindow 類別內新增此方法
    def open_log_folder(self):
        # 匯入 os 模組
        import os
        # 取得 logs 資料夾的絕對路徑
        log_path = os.path.abspath("logs")
        # 使用系統預設指令開啟資料夾視窗 (Windows 環境)
        os.startfile(log_path)

    # 恢復所有 UI 元件為預設狀態
    def reset_ui(self):
        self.btn_start.setEnabled(True)
        self.combo_category.setEnabled(True)
        self.combo_stage.setEnabled(True)
        self.btn_stop.setEnabled(False)
        for combos in self.team_combos:
            combos["char"].setEnabled(True)
            combos["arch"].setEnabled(True)
        print("[系統] 任務結束，介面已解鎖。")


if __name__ == "__main__":
    os.makedirs("logs/fail_cases", exist_ok=True)
    app = QApplication(sys.argv)
    app.setStyle("Fusion") 
    window = MainWindow()
    window.show()
    sys.exit(app.exec())