import re
import os
import requests
import argparse # 引入 argparse 模組 (Introduce the argparse module)
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase
import xml.etree.ElementTree as ET

def ensure_output_dir(output_dir):
    """
    確保輸出目錄存在，如果不存在則創建。
    (Ensure output directory exists, create if it doesn't.)

    Args:
        output_dir (str): 輸出目錄路徑。 (Output directory path.)
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

def extract_doi_from_reference(reference):
    """
    從參考文獻中提取 DOI。
    (Extract DOI from reference.)

    Args:
        reference (str): 參考文獻文字。 (Reference text.)

    Returns:
        str: DOI 如果找到，否則返回 None。 (DOI if found, None otherwise.)
    """
    # 更新 DOI 的正則表達式模式
    # (Update regular expression patterns for DOI)
    doi_patterns = [
        r'<https?://doi\.org/([^>]+)>',     # matches <https://doi.org/xxx>
        r'https?://doi\.org/([^\s<>]+)',    # matches https://doi.org/xxx
        r'doi\.org/([^\s<>]+)',             # matches doi.org/xxx
        r'https?://dx\.doi\.org/([^\s<>]+)', # matches https://dx.doi.org/xxx
        r'doi:\s*([^\s<>]+)',               # matches doi: xxx
        r'DOI:\s*([^\s<>]+)',               # matches DOI: xxx
        r'\. doi:?\s*([^\s<>]+)',           # matches . doi: xxx (with period)
        r'\. DOI:?\s*([^\s<>]+)',           # matches . DOI: xxx (with period)
    ]
    
    for pattern in doi_patterns:
        match = re.search(pattern, reference, re.IGNORECASE)  # 添加忽略大小寫的標誌
        if match:
            doi = match.group(1).strip('.')  # 移除結尾的句點
            # 確保 DOI 是有效的格式
            if '/' in doi and not any(c in doi for c in ['<', '>', ' ']):
                print(f"找到 DOI: {doi}")  # 添加偵錯輸出
                print(f"(Found DOI: {doi})")
                return doi
    return None

def extract_references_from_file(filepath):
    """
    從文件中提取參考文獻部分。
    (Extract the references section from the file.)

    Args:
        filepath (str): 文件路徑。 (The path to the file.)

    Returns:
        list: 參考文獻列表，每個元素包含參考文獻文字和識別碼（PMID 或 DOI）。
        (List of references, each containing reference text and identifier (PMID or DOI).)
    """
    references = []
    in_references = False
    current_reference = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for i, line in enumerate(lines):
        # 修改參考文獻區段的識別方式，忽略大小寫
        # (Modify how we identify the references section, case-insensitive)
        ref_headers = ['**references**', '**reference**', 'references', 'reference', '# references', '# reference']
        if any(line.strip().lower() == header for header in ref_headers):
            print(f"找到參考文獻區段標記：{line.strip()}")
            print(f"(Found reference section marker: {line.strip()})")
            in_references = True
            continue
            
        if in_references:
            # 如果遇到新的參考文獻（支援多種格式：[1]、1.、1)）
            # (If we encounter a new reference (supports multiple formats: [1], 1., 1)))
            if re.match(r'^\[?\d+[\.\)\]]', line.strip()):  # 修改這行以支援 [1] 格式
                if current_reference:
                    ref_text = ''.join(current_reference)
                    doi = extract_doi_from_reference(ref_text)
                    pmid = extract_pmids_from_file(ref_text)
                    if doi or pmid:  # 只有在找到 DOI 或 PMID 時才添加
                        references.append({
                            'text': ref_text,
                            'doi': doi,
                            'pmid': pmid
                        })
                current_reference = [line]
            # 如果是參考文獻的延續行
            # (If it's a continuation line of the current reference)
            elif current_reference and line.strip():
                current_reference.append(line)
            # 如果遇到新的標題（以 # 開頭），結束參考文獻區段
            # (If we encounter a new heading (starts with #), end the references section)
            elif line.strip().startswith('#') and not any(header in line.lower() for header in ref_headers):
                in_references = False
            # 如果遇到連續兩個空行，可能是參考文獻區段結束
            # (If we encounter two consecutive empty lines, it might be the end of references section)
            elif not line.strip() and not current_reference:
                continue
    
    # 處理最後一個參考文獻
    # (Process the last reference)
    if current_reference:
        ref_text = ''.join(current_reference)
        doi = extract_doi_from_reference(ref_text)
        pmid = extract_pmids_from_file(ref_text)
        if doi or pmid:  # 只有在找到 DOI 或 PMID 時才添加
            references.append({
                'text': ref_text,
                'doi': doi,
                'pmid': pmid
            })
    
    return references

def save_references_to_file(references, filepath):
    """
    將參考文獻儲存到檔案。
    (Save references to a file.)

    Args:
        references (list): 參考文獻列表，每個元素是包含文字和識別碼的字典。
                         (List of references, each element is a dictionary containing text and identifiers.)
        filepath (str): 輸出檔案路徑。 (The output file path.)
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("# References\n\n")
        for ref in references:
            f.write(ref['text'])  # 寫入參考文獻文字 (Write reference text)
            f.write("\n")
            # 如果有 DOI，寫入 DOI 資訊 (If DOI exists, write DOI information)
            if ref.get('doi'):
                f.write(f"DOI: {ref['doi']}\n")
            f.write("\n")  # 在每個參考文獻之間加入空行 (Add empty line between references)

def extract_pmids_from_file(reference):
    """
    從參考文獻中提取 PMID。
    (Extract PMID from reference.)

    Args:
        reference (str): 參考文獻文字。 (Reference text.)

    Returns:
        str: PMID 如果找到，否則返回 None。 (PMID if found, None otherwise.)
    """
    # 匹配 PMID 的正則表達式模式
    # (Regular expression pattern to match PMID)
    pmid_patterns = [
        r'pubmed/(\d+)',           # matches pubmed/xxxxxxx
        r'PMID:?\s*(\d+)',         # matches PMID: xxxxxxx or PMID xxxxxxx
        r'PubMed ID:?\s*(\d+)',    # matches PubMed ID: xxxxxxx
    ]
    
    for pattern in pmid_patterns:
        match = re.search(pattern, reference)
        if match:
            return match.group(1)
    return None

def detect_file_format(filepath):
    """
    檢測文件格式是否為 EAU 格式。
    (Detect if the file is in EAU format.)

    Args:
        filepath (str): 文件路徑。 (The path to the file.)

    Returns:
        str: 'eau' 或 'standard'。 ('eau' or 'standard'.)
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    # 檢查前幾行是否符合 EAU 格式的特徵
    # (Check if the first few lines match EAU format characteristics)
    for i in range(min(10, len(lines))):
        line = lines[i].strip()
        # 檢查是否有類似 "1.Author, et al." 的格式
        if re.match(r'^\d+\.[A-Za-z]', line):
            # 往下找幾行，看是否有 PubMed 連結
            for j in range(i + 1, min(i + 5, len(lines))):
                if 'pubmed.ncbi.nlm.nih.gov' in lines[j]:
                    return 'eau'
    return 'standard'

def extract_pmids_from_eau_file(filepath):
    """
    從 EAU 格式的文件中提取所有 PMID 和對應的參考文獻編號。
    (Extract all PMIDs and corresponding reference numbers from an EAU format file.)

    Args:
        filepath (str): 文件路徑。 (The path to the file.)

    Returns:
        list: 包含參考文獻資訊的字典列表。 (A list of dictionaries containing reference information.)
    """
    references = []
    current_ref = None
    reference_text = []
    in_references = False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # 檢查是否進入參考文獻區段
        if line.upper() == "REFERENCES" or line.upper() == "9. REFERENCES":
            in_references = True
            continue
            
        if not in_references:
            continue
            
        # 檢查是否為參考文獻編號開頭 (例如：1.Author 或 1. Author)
        ref_match = re.match(r'^(\d+)\.?\s*([^\.]+)', line)
        if ref_match:
            # 如果已有當前參考文獻，保存它
            if current_ref:
                current_ref['text'] = ' '.join(reference_text)
                references.append(current_ref)
            
            # 開始新的參考文獻
            reference_text = [line]
            current_ref = {
                'text': line,
                'ref_num': ref_match.group(1),
                'doi': None,
                'pmid': None
            }
            
            # 向前看幾行，尋找 PubMed URL
            for j in range(i + 1, min(i + 5, len(lines))):
                next_line = lines[j].strip()
                if 'pubmed.ncbi.nlm.nih.gov' in next_line:
                    pmid_match = re.search(r'pubmed\.ncbi\.nlm\.nih\.gov/(\d+)', next_line)
                    if pmid_match:
                        current_ref['pmid'] = pmid_match.group(1)
                        print(f"找到 PMID: {pmid_match.group(1)} 用於參考文獻 {current_ref['ref_num']}")
                        print(f"(Found PMID: {pmid_match.group(1)} for reference {current_ref['ref_num']})")
                        break
        
        # 檢查是否為 DOI
        elif current_ref and ('doi.org' in line or 'doi:' in line.lower()):
            doi = extract_doi_from_reference(line)
            if doi:
                current_ref['doi'] = doi
                print(f"找到 DOI: {doi} 用於參考文獻 {current_ref['ref_num']}")
                print(f"(Found DOI: {doi} for reference {current_ref['ref_num']})")
        
        # 如果是參考文獻的延續行
        elif current_ref and not line.startswith('http'):
            reference_text.append(line)
    
    # 添加最後一個參考文獻
    if current_ref:
        current_ref['text'] = ' '.join(reference_text)
        references.append(current_ref)
    
    # 顯示統計資訊
    total_refs = len(references)
    refs_with_pmid = sum(1 for ref in references if ref['pmid'])
    refs_with_doi = sum(1 for ref in references if ref['doi'])
    
    print(f"\n參考文獻統計：")
    print(f"(Reference statistics:)")
    print(f"總數 (Total): {total_refs}")
    print(f"有 PMID (With PMID): {refs_with_pmid}")
    print(f"有 DOI (With DOI): {refs_with_doi}")
    
    # 檢查遺漏的參考文獻
    missing_refs = []
    for ref in references:
        if not ref['pmid'] and not ref['doi']:
            missing_refs.append(ref['ref_num'])
    
    if missing_refs:
        print(f"\n警告：以下參考文獻沒有 PMID 或 DOI：")
        print(f"(Warning: The following references have no PMID or DOI:)")
        print(", ".join(missing_refs))
    
    return references

def fetch_bibtex_from_pmid(pmid):
    """
    使用 PMID 從 PubMed 獲取 BibTeX 格式的文獻資訊。
    (Fetches BibTeX-formatted literature information from PubMed using PMID.)

    Args:
        pmid (str): 文獻的 PMID。 (The PMID of the literature.)

    Returns:
        str: 文獻的 BibTeX 格式，如果出錯則返回 None。 (The BibTeX format of the literature, or None if an error occurs.)
    """
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "pubmed",
        "id": pmid,
        "rettype": "medline",
        "retmode": "text"
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # 檢查請求是否成功 (Check if the request was successful)

        # 將 MEDLINE 格式轉換為字典 (Convert MEDLINE format to a dictionary)
        medline_data = {}
        for line in response.text.splitlines():
            if line.startswith('PMID-'):
                current_key = 'PMID'
                medline_data[current_key] = line[6:].strip()
            elif line.startswith('  '):
                medline_data[current_key] += line.strip()
            elif '-' in line:
                current_key = line.split('-')[0].strip()
                medline_data[current_key] = line.split('-')[1].strip()

        # 將 MEDLINE 字典轉換為 BibTeX 字典 (Convert MEDLINE dictionary to BibTeX dictionary)
        bibtex_entry = {
            'ENTRYTYPE': 'article',
            'ID': medline_data.get('PMID', ''),
            'title': medline_data.get('TI', ''),
            'author': ' and '.join(medline_data.get('AU', '').split(';')),
            'journal': medline_data.get('JT', ''),
            'year': medline_data.get('DP', '')[:4],
            'volume': medline_data.get('VI', ''),
            'pages': medline_data.get('PG', ''),
            'abstract': medline_data.get('AB', ''),
            'keywords': medline_data.get('OT', ''),
            'doi': medline_data.get('AID', '').replace('[doi]', ''),
            'pmid': medline_data.get('PMID', '')
        }

        # 移除空值 (Remove empty values)
        bibtex_entry = {k: v for k, v in bibtex_entry.items() if v}

        # 使用 BibTexWriter 轉換為 BibTeX 格式 (Convert to BibTeX format using BibTexWriter)
        db = BibDatabase()
        db.entries = [bibtex_entry]
        writer = BibTexWriter()
        return writer.write(db)

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for PMID {pmid}: {e}")
        return None

def fetch_bibtex_from_doi(doi):
    """
    使用 DOI 從 CrossRef 獲取 BibTeX 格式的文獻資訊，並額外獲取摘要。
    (Fetches BibTeX-formatted literature information and abstract from CrossRef using DOI.)

    Args:
        doi (str): 文獻的 DOI。 (The DOI of the literature.)

    Returns:
        str: 文獻的 BibTeX 格式，如果出錯則返回 None。 (The BibTeX format of the literature, or None if an error occurs.)
    """
    # 設定超時時間（秒）(Set timeout in seconds)
    TIMEOUT = 10
    
    # 首先獲取 BibTeX
    headers_bibtex = {
        'Accept': 'application/x-bibtex',
        'User-Agent': 'BibTeX Extractor (mailto:your-email@example.com)'
    }
    
    # 使用 Crossref API 獲取 JSON 格式（包含摘要）
    headers_json = {
        'Accept': 'application/vnd.crossref.unixsd+xml',
        'User-Agent': 'BibTeX Extractor (mailto:your-email@example.com)'
    }
    
    # Crossref API URL
    crossref_api_url = f'https://api.crossref.org/works/{doi}'
    bibtex_url = f'https://doi.org/{doi}'
    
    try:
        # 獲取 BibTeX
        print(f"正在獲取 BibTeX 格式 (Fetching BibTeX format)...")
        response_bibtex = requests.get(bibtex_url, headers=headers_bibtex, timeout=TIMEOUT)
        response_bibtex.raise_for_status()
        bibtex = response_bibtex.text
        
        try:
            # 使用 Crossref API 獲取完整資訊
            print(f"正在獲取摘要 (Fetching abstract)...")
            response_json = requests.get(crossref_api_url, timeout=TIMEOUT)
            response_json.raise_for_status()
            data = response_json.json()
            
            # 從 Crossref API 回應中提取摘要
            if 'message' in data and 'abstract' in data['message']:
                abstract = data['message']['abstract']
                # 清理摘要文字（移除 HTML 標籤等）
                abstract = re.sub(r'<[^>]+>', '', abstract)
                abstract = re.sub(r'\s+', ' ', abstract).strip()
                
                # 移除最後的 }
                bibtex = bibtex.rstrip('}\n')
                # 添加摘要
                bibtex += f',\n  abstract = {{{abstract}}}\n}}'
                print(f"成功獲取摘要 (Successfully fetched abstract)")
            else:
                print(f"此 DOI 沒有提供摘要 (No abstract available for this DOI)")
                
        except (requests.exceptions.RequestException, ValueError) as e:
            # 如果獲取摘要失敗，仍然返回基本的 BibTeX
            print(f"警告：無法獲取摘要，但已獲得基本 BibTeX 資訊")
            print(f"(Warning: Could not fetch abstract, but basic BibTeX information is available)")
            print(f"錯誤訊息 (Error message): {str(e)}")
        
        return bibtex
        
    except requests.exceptions.Timeout:
        print(f"錯誤：獲取 DOI {doi} 的資訊超時")
        print(f"(Error: Timeout while fetching data for DOI {doi})")
        return None
    except requests.exceptions.RequestException as e:
        print(f"錯誤：獲取 DOI {doi} 的資訊失敗")
        print(f"(Error: Failed to fetch data for DOI {doi})")
        print(f"錯誤訊息 (Error message): {str(e)}")
        return None
    except Exception as e:
        print(f"未預期的錯誤：{str(e)}")
        print(f"(Unexpected error: {str(e)})")
        return None

def extract_text_from_jats(jats_xml):
    """
    從 JATS XML 中提取純文字摘要。
    (Extracts plain text abstract from JATS XML.)

    Args:
        jats_xml (str): JATS XML 格式的摘要。 (Abstract in JATS XML format.)

    Returns:
        str: 純文字摘要。 (Plain text abstract.)
    """
    try:
        root = ET.fromstring(jats_xml) # 使用 ET.fromstring 解析 XML 字串 (Parse XML string using ET.fromstring)
        # 尋找所有 <p> 標籤並提取其文字內容
        # (Find all <p> tags and extract their text content)
        paragraphs = root.findall(".//jats:p", namespaces={'jats': 'http://www.ncbi.nlm.nih.gov/JATS1'})
        abstract_text = ' '.join(paragraph.text for paragraph in paragraphs if paragraph.text)
        
        # 移除多餘的空白和換行符
        # (Remove extra whitespace and newline characters)
        abstract_text = re.sub(r'\s+', ' ', abstract_text).strip()
        
        return abstract_text
    except ET.ParseError:
        print("警告：無法解析 JATS XML，將返回原始 XML")
        print("(Warning: Could not parse JATS XML, returning raw XML)")
        return jats_xml

def save_bibtex_to_file(bibtex_entries, filepath):
    """
    將 BibTeX 格式的文獻資訊儲存到文件。
    (Saves BibTeX-formatted literature information to a file.)

    Args:
        bibtex_entries (list): 包含 BibTeX 格式文獻資訊的列表。 (A list containing BibTeX-formatted literature information.)
        filepath (str): 儲存 BibTeX 格式的文件路徑。 (The path to the file to save the BibTeX format.)
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        for bibtex_entry in bibtex_entries:
            f.write(bibtex_entry)
            f.write('\n')

def save_reference_map(ref_numbers, pmids, filepath):
    """
    儲存參考文獻編號和 PMID 的對照表。
    (Save reference number and PMID mapping.)

    Args:
        ref_numbers (list): 參考文獻編號列表。 (List of reference numbers.)
        pmids (list): PMID 列表。 (List of PMIDs.)
        filepath (str): 輸出檔案路徑。 (Output file path.)
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("參考文獻編號和 PMID 對照表\n")
        f.write("(Reference numbers and PMIDs mapping)\n\n")
        f.write("序號\t參考文獻編號\tPMID\n")
        f.write("(Index\tReference No.\tPMID)\n")
        f.write("-" * 40 + "\n")
        
        for i, (ref_num, pmid) in enumerate(zip(ref_numbers, pmids), 1):
            f.write(f"{i}\t{ref_num}\t{pmid}\n")

# 主程式 (Main program)
if __name__ == "__main__":
    # 建立 ArgumentParser 物件 (Create an ArgumentParser object)
    parser = argparse.ArgumentParser(description="從文件中提取 PMID 和 DOI 並產生 BibTeX 檔案。 (Extract PMIDs and DOIs from the file and generate a BibTeX file.)")

    # 新增一個命令列參數，用於指定輸入檔案的路徑 (Add a command-line argument for specifying the path to the input file)
    parser.add_argument("filepath", help="輸入檔案的路徑 (The path to the input file)")
    parser.add_argument("--output", default="references.bib", help="輸出的 BibTeX 檔案路徑 (Output BibTeX file path)")

    # 解析命令列參數 (Parse command-line arguments)
    args = parser.parse_args()

    # 設定輸入和輸出路徑 (Set input and output paths)
    input_file = args.filepath
    output_filepath = args.output
    output_dir = "output"

    # 確保輸出目錄存在 (Ensure output directory exists)
    ensure_output_dir(output_dir)
    
    # 檢測文件格式 (Detect file format)
    file_format = detect_file_format(input_file)
    
    # 根據文件格式提取參考文獻 (Extract references based on file format)
    if file_format == 'eau':
        print("檢測到 EAU 格式文件")
        print("(Detected EAU format file)")
        references = extract_pmids_from_eau_file(input_file)
    else:
        print("檢測到標準格式文件")
        print("(Detected standard format file)")
        references = extract_references_from_file(input_file)
        references_file = os.path.join(output_dir, "references.md")
        save_references_to_file(references, references_file)
        print(f"References saved to {references_file}")

    # 檢查是否有找到參考文獻 (Check if references were found)
    if not references:
        print("沒有找到任何參考文獻！")
        print("(No references found!)")
        exit(1)

    print(f"找到 {len(references)} 篇參考文獻")
    print(f"(Found {len(references)} references)")

    # 讓使用者選擇範圍 (Let user choose range)
    while True:
        try:
            print(f"\n請選擇要擷取的範圍 (1-{len(references)})：")
            print("(Please select the range to extract:)")
            start_idx = int(input(f"起始編號 (Start number, 1-{len(references)}): ")) - 1
            end_idx = int(input(f"結束編號 (End number, 1-{len(references)}): "))
            
            if 0 <= start_idx < len(references) and 0 < end_idx <= len(references) and start_idx < end_idx:
                print(f"\n您選擇的範圍：")
                print("(Your selected range:)")
                for i in range(start_idx, end_idx):
                    ref = references[i]
                    if ref.get('doi'):
                        print(f"參考文獻 {i+1}: DOI {ref['doi']}")
                    elif ref.get('pmid'):
                        print(f"參考文獻 {i+1}: PMID {ref['pmid']}")
                    else:
                        print(f"參考文獻 {i+1}: 無識別碼")
                
                confirm = input("\n確認要處理這些文獻？(y/n): ")
                if confirm.lower() == 'y':
                    break
            else:
                print("\n錯誤：請輸入有效的範圍！")
                print("(Error: Please enter a valid range!)")
        except ValueError:
            print("\n錯誤：請輸入數字！")
            print("(Error: Please enter numbers!)")

    selected_references = references[start_idx:end_idx]
    print(f"\n將擷取第 {start_idx+1} 到第 {end_idx} 筆文獻")
    print(f"(Will extract references from {start_idx+1} to {end_idx})")

    # 獲取並轉換為 BibTeX 格式 (Fetch and convert to BibTeX format)
    bibtex_entries = []
    for i, ref in enumerate(selected_references, 1):
        print(f"\n處理第 {i}/{len(selected_references)} 筆參考文獻")
        print(f"(Processing {i}/{len(selected_references)} reference)")
        
        if ref.get('doi'):
            print(f"使用 DOI: {ref['doi']}")
            print(f"(Using DOI: {ref['doi']})")
            bibtex_entry = fetch_bibtex_from_doi(ref['doi'])
        elif ref.get('pmid'):
            print(f"使用 PMID: {ref['pmid']}")
            print(f"(Using PMID: {ref['pmid']})")
            bibtex_entry = fetch_bibtex_from_pmid(ref['pmid'])
        else:
            print("警告：無法找到 DOI 或 PMID")
            print("(Warning: Could not find DOI or PMID)")
            continue
            
        if bibtex_entry:
            bibtex_entries.append(bibtex_entry)
        else:
            print(f"警告：無法擷取參考文獻資訊")
            print(f"(Warning: Failed to fetch reference information)")

    # 儲存 BibTeX 格式到文件 (Save BibTeX format to a file)
    if bibtex_entries:
        output_path = os.path.join(output_dir, output_filepath)
        save_bibtex_to_file(bibtex_entries, output_path)
        print(f"\nBibTeX 條目已儲存至 {output_path}")
        print(f"(BibTeX entries saved to {output_path})")
    else:
        print("\n錯誤：沒有成功擷取到任何 BibTeX 條目！")
        print("(Error: No BibTeX entries were successfully retrieved!)")
