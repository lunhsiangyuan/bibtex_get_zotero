from pyzotero import zotero
import os

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
collection_id = "DGSGF8QL"

###############

def main():
    try:
        # 初始化 Zotero API (Initialize Zotero API)
        zot = zotero.Zotero(library_id, library_type, api_key)
        print("Successfully connected to Zotero!")

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
        items = zot.collection_items(collection_id)
        print(f"\nNumber of items found in collection: {len(items)}")

        # 下載文獻 (Download documents)
        download_count = 0
        for item in items:
            try:
                # 取得文獻標題 (Get document title)
                title = item['data'].get('title', 'Untitled')
                print(f"\nProcessing: {title}")
                
                # 取得附件 (Get attachments)
                attachments = zot.children(item['key'])
                
                # 處理每個附件 (Process each attachment)
                for attachment in attachments:
                    if attachment['data'].get('contentType') == 'application/pdf':
                        filename = attachment['data'].get('filename', 'document.pdf')
                        print(f"Found PDF: {filename}")
                        
                        # 建立安全的檔案名稱 (Create safe filename)
                        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_'))
                        output_path = os.path.join(output_dir, f"{safe_title}_{filename}")
                        
                        # 下載 PDF (Download PDF)
                        try:
                            with open(output_path, 'wb') as f:
                                f.write(zot.file(attachment['key']))
                            print(f"Successfully downloaded: {output_path}")
                            download_count += 1
                        except Exception as e:
                            print(f"Error downloading {filename}: {e}")
                        
            except Exception as e:
                print(f"Error processing item: {e}")

        print(f"\nDownload completed! Total files downloaded: {download_count}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()