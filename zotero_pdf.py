from pyzotero import zotero
import os
import re

###############   設定專區 (Configuration Section)
# Zotero API 金鑰 (API Key)
api_key = "tV6O2BcZhgBosEsY6kBvtXbx"
# Zotero 使用者 ID (User ID from Zotero website Settings->Feeds/API)
library_id = 319156
# Zotero 資料庫類型 (Library type - 'user' for personal library)
library_type = 'user'
# 匯出目錄 (Output directory)
output_dir = "zotero_pdf_output"
# 指定要抓取的資料夾 ID (Specify collection ID to fetch)
collection_id = "UWPW944U"

###############

def create_safe_filename(title, max_length=50):
    """建立安全且較短的檔案名稱 (Create safe and shorter filename)
    
    Args:
        title (str): 原始標題
        max_length (int): 最大長度（預設50字元）
    
    Returns:
        str: 安全的檔案名稱
    """
    # 移除特殊字元，只保留英文字母、數字和空格 (Remove special characters)
    safe_title = re.sub(r'[^\w\s-]', '', title)
    # 將多個空格替換為單個空格 (Replace multiple spaces with single space)
    safe_title = re.sub(r'\s+', ' ', safe_title).strip()
    # 如果標題太長，只取前max_length個字元 (If title is too long, only take first max_length characters)
    if len(safe_title) > max_length:
        safe_title = safe_title[:max_length].strip()
    return safe_title

def get_all_items(zot, collection_id):
    """取得資料夾中的所有項目，處理分頁問題 (Get all items from collection, handling pagination)
    
    Args:
        zot: Zotero API 實例
        collection_id: 資料夾 ID
    
    Returns:
        list: 所有項目的列表
    """
    all_items = []
    start = 0
    limit = 100  # Zotero API 的每頁限制

    while True:
        items = zot.collection_items(collection_id, start=start, limit=limit)
        if not items:
            break
        all_items.extend(items)
        start += limit
        print(f"Retrieved {len(all_items)} items so far...")

    return all_items

def main():
    try:
        # 初始化 Zotero API (Initialize Zotero API)
        zot = zotero.Zotero(library_id, library_type, api_key)
        print("Successfully connected to Zotero!")

        # 測試 API 權限 (Test API permissions)
        try:
            user_info = zot.key_info()
            print(f"\nAPI Key permissions: {user_info}")
        except Exception as e:
            print(f"Error checking API permissions: {e}")

        # 建立輸出目錄 (Create output directory if not exists)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")

        # 取得所有資料夾 (Get all collections)
        collections = zot.collections()
        print("\nCollections:")
        for collection in collections:
            print(f"  Collection Name: {collection['data']['name']}, Collection ID: {collection['key']}")

        # 取得指定資料夾中的所有文獻 (Get all items from specified collection)
        print("\nRetrieving all items from collection...")
        items = get_all_items(zot, collection_id)
        print(f"Number of items found in collection: {len(items)}")

        # 計算 PDF 附件總數 (Count total PDF attachments)
        pdf_count = 0
        for item in items:
            if (item['data'].get('itemType') == 'attachment' and 
                item['data'].get('contentType') == 'application/pdf'):
                pdf_count += 1
        print(f"\nTotal PDF attachments found: {pdf_count}")

        # 顯示所有項目類型 (Show all item types)
        item_types = {}
        for item in items:
            item_type = item['data'].get('itemType', 'unknown')
            if item_type not in item_types:
                item_types[item_type] = 0
            item_types[item_type] += 1
        
        print("\nItem types in collection:")
        for item_type, count in item_types.items():
            print(f"  {item_type}: {count} items")

        # 下載文獻 (Download documents)
        download_count = 0
        error_count = 0  # 追蹤下載失敗的數量
        processed_items = set()  # 用來追蹤已處理的項目

        for item in items:
            try:
                # 如果是附件，找到其父項目 (If it's an attachment, find its parent)
                if item['data'].get('itemType') == 'attachment':
                    parent_key = item['data'].get('parentItem')
                    if parent_key and parent_key not in processed_items:
                        try:
                            parent_item = zot.item(parent_key)
                            title = parent_item['data'].get('title', 'Untitled')
                            print(f"\nProcessing parent item: {title}")
                            print(f"Parent item type: {parent_item['data'].get('itemType')}")
                            
                            # 標記父項目為已處理 (Mark parent as processed)
                            processed_items.add(parent_key)
                            
                            # 下載 PDF (Download PDF)
                            if item['data'].get('contentType') == 'application/pdf':
                                try:
                                    # 取得作者和年份 (Get author and year if available)
                                    creators = parent_item['data'].get('creators', [])
                                    first_author = 'Unknown'
                                    for creator in creators:
                                        if 'lastName' in creator:
                                            first_author = creator['lastName']
                                            break
                                    
                                    year = parent_item['data'].get('date', '')[:4] if parent_item['data'].get('date') else ''
                                    
                                    # 建立檔案名稱 (Create filename)
                                    safe_title = create_safe_filename(title)
                                    if year:
                                        filename = f"{first_author}_{year}_{safe_title}.pdf"
                                    else:
                                        filename = f"{first_author}_{safe_title}.pdf"
                                    
                                    output_path = os.path.join(output_dir, filename)
                                    print(f"Saving as: {filename}")
                                    
                                    pdf_content = zot.file(item['key'])
                                    print(f"PDF content size: {len(pdf_content) if pdf_content else 0} bytes")
                                    
                                    if pdf_content:
                                        with open(output_path, 'wb') as f:
                                            f.write(pdf_content)
                                        print(f"Successfully downloaded: {output_path}")
                                        download_count += 1
                                    else:
                                        print("No PDF content received")
                                        error_count += 1
                                except Exception as e:
                                    print(f"Error downloading PDF: {str(e)}")
                                    error_count += 1
                        except Exception as e:
                            print(f"Error processing parent item: {str(e)}")
                            error_count += 1
                
            except Exception as e:
                print(f"Error processing item: {str(e)}")
                error_count += 1

        print(f"\nDownload completed!")
        print(f"Total PDF attachments found: {pdf_count}")
        print(f"Successfully downloaded: {download_count}")
        print(f"Failed downloads: {error_count}")

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()