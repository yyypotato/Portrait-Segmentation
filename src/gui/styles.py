class Styles:
    # 通用按钮样式
    BUTTON_STYLE = """
        QPushButton {
            background-color: #2d3436;
            color: white;
            border: none;
            border-radius: 8px;
            font-family: "Microsoft YaHei";
            font-size: 16px;
            padding: 10px 20px;
        }
        QPushButton:hover {
            background-color: #0984e3;
        }
        QPushButton:pressed {
            background-color: #0c2461;
        }
    """
    # 菜单页大按钮样式
    MENU_BUTTON_STYLE = """
        QPushButton {
            background-color: rgba(255, 255, 255, 0.1);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 15px;
            font-family: "Microsoft YaHei";
            font-size: 18px;
            font-weight: bold;
            padding: 15px;
        }
        QPushButton:hover {
            background-color: rgba(255, 255, 255, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.8);
            font-size: 19px; /* 悬停微放大 */
        }
    """

    # 标题样式
    TITLE_STYLE = """
        QLabel {
            color: white;
            font-family: "Microsoft YaHei";
            font-size: 36px;
            font-weight: bold;
            background-color: transparent;
        }
    """
    
    # 页面背景（深色渐变模拟）
    MAIN_BG_COLOR = "#2d3436"