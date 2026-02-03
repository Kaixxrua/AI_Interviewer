# import_kb.py
import os
import sys

# 1. 设置路径，确保能找到 app 模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.rag_service import add_document_to_kb

# 2. 配置你的数据文件夹路径
DATA_DIR = "./rag_source"


def import_all_recursive():
    if not os.path.exists(DATA_DIR):
        print(f"❌ 错误：找不到文件夹 {DATA_DIR}")
        return

    print(f"🚀 开始递归扫描 {DATA_DIR} 下的所有文件...\n")

    success_count = 0
    total_files_found = 0

    # os.walk 是递归的神器，它会遍历每一层目录
    for root, dirs, files in os.walk(DATA_DIR):

        # 可以在这里忽略一些不需要的文件夹，比如图片文件夹或 .git
        if ".git" in root or "images" in root:
            continue

        for filename in files:
            file_path = os.path.join(root, filename)

            # 1. 过滤文件类型
            ext = os.path.splitext(filename)[1].lower()
            if ext not in [".md", ".txt", ".pdf"]:
                # 默默跳过非目标文件，不打印日志以免刷屏
                continue

            total_files_found += 1

            # 打印相对路径，让你知道处理到哪儿了
            relative_path = os.path.relpath(file_path, DATA_DIR)
            print(f"📄 [{total_files_found}] 处理中: {relative_path} ...")

            try:
                # 2. 调用入库函数
                # 注意：这里我们把 relative_path 作为 source_name
                # 这样以后检索时，你知道它是 "Java/多线程.md" 而不是光知道 "多线程.md"
                chunks = add_document_to_kb(file_path, source_name=relative_path)

                if chunks > 0:
                    success_count += 1
            except Exception as e:
                print(f"❌ 失败: {filename} - {str(e)}")

    print(f"\n🎉 全部完成！")
    print(f"扫描到文件: {total_files_found}")
    print(f"成功入库: {success_count}")


if __name__ == "__main__":
    import_all_recursive()
