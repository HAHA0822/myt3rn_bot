#!/bin/bash

# 功能：安装 Python 和 pip
install_python() {
    echo "正在检查 Python 和 pip 是否安装..."
    if command -v python3 &>/dev/null; then
        echo "Python 3 已安装。"
    else
        echo "Python 3 未安装，正在安装..."
        sudo apt update
        sudo apt install -y python3 python3-pip
    fi
}


# 功能：设置环境变量
setup_environment() {
    read -p "请输入您的第一个私钥 / Enter your private key: " PRIVATE_KEY1
    export MY_PRIVATE_KEY1=$PRIVATE_KEY1
    read -p "请输入您的第二个私钥 / Enter your private key: " PRIVATE_KEY2
    export MY_PRIVATE_KEY2=$PRIVATE_KEY2
    read -p "请输入您的第三个私钥 / Enter your private key: " PRIVATE_KEY3
    export MY_PRIVATE_KEY3=$PRIVATE_KEY3
    read -p "请输入您的第四个私钥 / Enter your private key: " PRIVATE_KEY4
    export MY_PRIVATE_KEY4=$PRIVATE_KEY4
    read -p "请输入您的第五个私钥 / Enter your private key: " PRIVATE_KEY5
    export MY_PRIVATE_KEY5=$PRIVATE_KEY5
    # export MY_ADDRESS=$ADDRESS
    echo "私钥已设置为环境变量 MY_PRIVATE_KEY。"
}

# 功能：启动 Python 脚本
start_python_script() {
    local script_path="./bot.py"  # 请替换为您的 Python 脚本路径
    pm2 start python3 --name t3rn_bot -- $script_path
    pm2 save
    echo "Python 脚本已通过 pm2 启动。"
}

# 功能：查看日志
view_logs() {
    pm2 logs t3rn_bot --lines 50 
}

# 主菜单
main_menu() {
    while true; do
        clear
        echo "=============================================="
        echo "请选择一个选项: / Please select an option:"
        echo "1. 设置私钥 / Set private key"
        echo "2. 启动 Python 脚本 / Start Python script"
        echo "3. 查看日志 / View logs"
        echo "4. 退出 / Exit"
        echo "=============================================="

        read -p "请输入选项 (1-4): / Enter your choice (1-4): " choice

        case $choice in
            1)
                setup_environment
                ;;
            2)
                start_python_script
                ;;
            3)
                view_logs
                ;;
            4)
                echo "退出脚本。/ Exiting the script."
                exit 0
                ;;
            *)
                echo "无效选项，请重新输入。/ Invalid option, please try again."
                ;;
        esac
    done
}

# 要检查的库
packages=("web3" "colorama")

install_python  # 调用安装 Python 函数

for package in "${packages[@]}"; do
    if python -c "import $package" &> /dev/null; then
        echo "$package 已安装。"
    else
        echo "$package 未安装，正在安装..."
        pip install "$package"
    fi
done

# 启动主菜单
main_menu
