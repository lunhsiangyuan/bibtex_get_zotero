# BibTeX 參考文獻擷取工具 (BibTeX Reference Extractor)

這個工具可以從文件中提取 PMID 和 DOI 並產生 BibTeX 格式的參考文獻。
(This tool extracts PMIDs and DOIs from documents and generates BibTeX format references.)

## 功能特點 (Features)

### BibTeX 擷取功能 (BibTeX Extraction Features)
- 支援 EAU 格式和標準格式的文件 (Supports both EAU format and standard format documents)
- 自動檢測文件格式 (Automatically detects document format)
- 支援從參考文獻中提取 DOI (Supports DOI extraction from references)
- 支援從參考文獻中提取 PMID (Supports PMID extraction from references)
- 可選擇要處理的參考文獻範圍 (Allows selection of reference range to process)
- 產生 BibTeX 格式的輸出 (Generates BibTeX format output)
- 產生參考文獻對照表 (Generates reference comparison table)

### Zotero PDF 下載功能 (Zotero PDF Download Features)
- 連接 Zotero API 下載 PDF (Connect to Zotero API for PDF downloads)
- 顯示所有可用的文獻集合 (Display all available collections)
- 自動下載指定集合中的 PDF 檔案 (Automatically download PDFs from specified collections)
- 智能檔案命名和管理 (Smart file naming and management)

## 安裝方法 (Installation)

1. 複製專案 (Clone the project)
```bash
git clone [repository-url]
cd [project-directory]
```

2. 安裝相依套件 (Install dependencies)
```bash
pip install -r requirements.txt
```

## 使用方法 (Usage)

### BibTeX 擷取工具 (BibTeX Extractor)
```bash
# 基本使用方法 (Basic usage)
python get_bibtex.py input_file.md

# 指定輸出檔案 (Specify output file)
python get_bibtex.py input_file.md --output references.bib
```

### Zotero PDF 下載工具 (Zotero PDF Downloader)
```bash
# 下載指定集合中的 PDF (Download PDFs from specified collection)
python zotero_pdf.py
```

## 設定說明 (Configuration)

### Zotero API 設定 (Zotero API Settings)
在 `zotero_pdf.py` 中設定以下參數：
- `api_key`: Zotero API 金鑰 (從 Zotero 網站的設定中獲取)
- `library_id`: Zotero 使用者 ID
- `library_type`: 資料庫類型 (個人使用者設為 'user')
- `collection_id`: 要下載的文獻集合 ID

## 輸出檔案 (Output Files)

### BibTeX 工具輸出 (BibTeX Tool Output)
1. `output/references.bib`: BibTeX 格式的參考文獻
2. `output/reference_map.txt`: 參考文獻編號和識別碼對照表
3. `output/references.md`: 原始參考文獻列表

### Zotero PDF 工具輸出 (Zotero PDF Tool Output)
- `zotero_pdf_output/`: 下載的 PDF 檔案存放目錄

## 注意事項 (Notes)

- 需要網路連線來擷取 PubMed 和 CrossRef 資料 (Internet connection required for PubMed and CrossRef data retrieval)
- 大量擷取時建議分批處理 (Recommended to process in batches for large numbers of references)
- 確保輸入檔案使用 UTF-8 編碼 (Ensure input files are UTF-8 encoded)
- 使用 CrossRef API 時建議提供有效的電子郵件地址 (Recommended to provide a valid email address when using CrossRef API) 