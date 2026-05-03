# config.py

# 定義設定檔的儲存檔名，用來記憶使用者的介面選擇
CONFIG_FILE = "bot_config.json"

# 定義下拉式選單中可供選擇的隊員名稱清單
CHARACTERS = ["無/不更改", "奈音", "修女", "麥格納", "娜嘉", "米卡", "奧斯卡"]

# 定義下拉式選單中可供選擇的存檔標籤清單，對應遊戲內的星號
ARCHIVES = ["不切換", "星號 1", "星號 2", "星號 3"]

# 雙層字典架構，儲存所有關卡對應的圖片檔名
STAGE_DATA = {
    "成長": {
        "單元幣": {"banner": "banner_growth.png", "stage": "stage_coin.png"},
        "戰鬥員升級": {"banner": "banner_growth.png", "stage": "stage_fighter.png"},
        "夥伴升級": {"banner": "banner_growth.png", "stage": "stage_partner.png"}
    },
    "戰鬥員": {
        "決鬥家": {"banner": "banner_fighter.png", "stage": "fighter_duelist.png"},
        "先鋒": {"banner": "banner_fighter.png", "stage": "fighter_vanguard.png"},
        "遊俠": {"banner": "banner_fighter.png", "stage": "fighter_ranger.png"},
        "獵人": {"banner": "banner_fighter.png", "stage": "fighter_hunter.png"},
        "心靈術士": {"banner": "banner_fighter.png", "stage": "fighter_psychic.png"},
        "控制師": {"banner": "banner_fighter.png", "stage": "fighter_controller.png"}
    },
    "夥伴": {
        "決鬥家": {"banner": "banner_partner.png", "stage": "partner_duelist.png"},
        "先鋒": {"banner": "banner_partner.png", "stage": "partner_vanguard.png"},
        "遊俠": {"banner": "banner_partner.png", "stage": "partner_ranger.png"},
        "獵人": {"banner": "banner_partner.png", "stage": "partner_hunter.png"},
        "心靈術士": {"banner": "banner_partner.png", "stage": "partner_psychic.png"},
        "控制師": {"banner": "banner_partner.png", "stage": "partner_controller.png"}
    },
    "潛力": {
        "熱情": {"banner": "banner_potential.png", "stage": "stage_passion.png"},
        "秩序": {"banner": "banner_potential.png", "stage": "stage_order.png"},
        "本能": {"banner": "banner_potential.png", "stage": "stage_instinct.png"},
        "虛無": {"banner": "banner_potential.png", "stage": "stage_void.png"},
        "正義": {"banner": "banner_potential.png", "stage": "stage_justice.png"}
    }
}