# 論文編譯指南 (Compilation Guide)

## 系統要求 (Requirements)

- **macOS** with MacTeX 2025 installed
- **XeLaTeX** compiler (included in MacTeX)
- **BibTeX** bibliography tool (NOT biber)
- **Chinese Font**: Kaiti TC (Mac built-in)

## 快速開始 (Quick Start)

### 方法 1: 使用終端機編譯 (Terminal Compilation)

```bash
# 1. 清理舊的輔助檔案
rm -f *.aux *.bbl *.blg *.log *.out *.toc *.lof *.lot *.synctex.gz

# 2. 完整編譯流程 (4 步驟)
xelatex -synctex=1 -interaction=nonstopmode main.tex
bibtex main              # ⚠️ 注意：使用 bibtex，不是 biber！
xelatex -synctex=1 -interaction=nonstopmode main.tex
xelatex -synctex=1 -interaction=nonstopmode main.tex

# 3. 開啟 PDF
open main.pdf
```

### 方法 2: 使用 VS Code + LaTeX Workshop

#### 安裝與設定

1. 安裝 VS Code 擴充套件：**LaTeX Workshop**
2. 在 VS Code 設定中加入：

```json
{
    "latex-workshop.latex.tools": [
        {
            "name": "xelatex",
            "command": "xelatex",
            "args": [
                "-synctex=1",
                "-interaction=nonstopmode",
                "-file-line-error",
                "%DOC%"
            ]
        },
        {
            "name": "bibtex",
            "command": "bibtex",
            "args": ["%DOCFILE%"]
        }
    ],
    "latex-workshop.latex.recipes": [
        {
            "name": "xelatex -> bibtex -> xelatex*2",
            "tools": ["xelatex", "bibtex", "xelatex", "xelatex"]
        }
    ],
    "latex-workshop.view.pdf.viewer": "tab"
}
```

#### 使用快捷鍵

- **Cmd + S**: 儲存並自動編譯
- **Cmd + Option + B**: 手動建置
- **Cmd + Option + V**: 開啟 PDF 預覽
- **Cmd + 滑鼠左鍵**: 從程式碼跳轉到 PDF (SyncTeX)
- **Cmd + 滑鼠左鍵 (在 PDF)**: 從 PDF 跳轉到程式碼

## 常見問題排解 (Troubleshooting)

### ❌ 問題 1: "xelatex: command not found"

**原因**: MacTeX 的 PATH 沒有載入

**解決方法**:
```bash
# 臨時解決 (當前終端機)
eval "$(/usr/libexec/path_helper)"

# 永久解決 (加入 ~/.zshrc)
echo 'eval "$(/usr/libexec/path_helper)"' >> ~/.zshrc
source ~/.zshrc
```

### ❌ 問題 2: PDF 只有一頁 / 中文字不顯示

**可能原因**:
1. **使用了 biber 而不是 bibtex** ⚠️
2. 字體設定錯誤（TW-Kai 在 Mac 上不存在）

**解決方法**:
```bash
# 1. 確認 covers/load_env.tex 第 9 行是：
\setCJKmainfont[AutoFakeBold={4}, AutoFakeSlant=0.2]{Kaiti TC}

# 2. 確認編譯命令使用 bibtex（不是 biber）
bibtex main  # ✅ 正確
# biber main  # ❌ 錯誤！

# 3. 清理所有輔助檔案後重新編譯
rm -f *.aux *.bbl *.blg *.log *.out *.toc *.lof *.lot *.synctex.gz
xelatex -synctex=1 -interaction=nonstopmode main.tex
bibtex main
xelatex -synctex=1 -interaction=nonstopmode main.tex
xelatex -synctex=1 -interaction=nonstopmode main.tex
```

### ❌ 問題 3: Font warning 訊息

如果看到字體警告，可以嘗試其他 Mac 內建字體：

```latex
% 方案 1 (預設): 楷體
\setCJKmainfont[AutoFakeBold={4}, AutoFakeSlant=0.2]{Kaiti TC}

% 方案 2: 宋體
\setCJKmainfont[AutoFakeBold={4}, AutoFakeSlant=0.2]{Songti TC}

% 方案 3: 黑體（較現代）
\setCJKmainfont[AutoFakeBold={4}, AutoFakeSlant=0.2]{PingFang TC}
```

## 檔案結構 (File Structure)

```
Roy_Thesis/
├── main.tex                    # 主檔案（論文資訊設定）
├── ref.bib                     # 參考文獻資料庫
├── covers/
│   ├── load_env.tex           # 套件與字體設定 ⚙️
│   ├── front_var.tex          # 封面
│   ├── inside_var.tex         # 書名頁
│   ├── toc_var.tex            # 目錄設定
│   └── logo2.pdf              # 陽明交大浮水印
└── Sections/
    ├── 0.1.Acknowledgement.tex    # 致謝
    ├── 0.2.Abstract_chinese.tex   # 中文摘要
    ├── 0.3.Abstract.tex           # 英文摘要
    ├── 1.Introduction.tex         # 第一章
    ├── 2.Relatedwork.tex          # 第二章
    ├── 3.Architecture.tex         # 第三章
    ├── 4.Methodology.tex          # 第四章
    ├── 5.Evaluation.tex           # 第五章
    └── 6.Conclusion.tex           # 第六章
```

## 編輯內容 (Editing Content)

### 修改個人資訊

編輯 `main.tex` 第 13-54 行：
- 論文名稱 (中英文)
- 學生姓名
- 指導教授
- 系所資訊
- 日期

### 撰寫論文內容

直接編輯 `Sections/` 目錄下的各章節檔案：
- `1.Introduction.tex` - 緒論
- `2.Relatedwork.tex` - 文獻探討
- `3.Architecture.tex` - 系統架構
- `4.Methodology.tex` - 研究方法
- `5.Evaluation.tex` - 結果與討論
- `6.Conclusion.tex` - 結論

### 管理參考文獻

編輯 `ref.bib` 檔案，格式範例：

```bibtex
@article{author2024,
    author = {作者名},
    title = {論文標題},
    journal = {期刊名稱},
    year = {2024},
    volume = {1},
    pages = {1--10}
}
```

在內文中引用：`\cite{author2024}`

## 目前論文資訊 (Current Thesis Info)

- **學生**: 羅頤 (Lo, Yi)
- **指導教授**: 黃宜侯 (Huang, Alex YiHou)
- **系所**: 管理學院 資訊管理與財務金融學系財務金融碩士班
- **論文題目**: 圖神經網絡在股票投資組合優化中的應用：以產業關係與市場互動為基礎
- **關鍵字**: 圖注意力網絡、股票收益率預測、量化投資策略
- **日期**: 2026 年 6 月

## Git 操作 (Git Operations)

```bash
# 檢視修改狀態
git status

# 拉取最新版本
git pull origin claude/summarize-content-011CUjCP2EB5QHBCzzRCp392

# 提交變更
git add .
git commit -m "更新論文內容"
git push -u origin claude/summarize-content-011CUjCP2EB5QHBCzzRCp392
```

## 參考資源 (References)

- [陽明交大論文格式規範](https://aa.nycu.edu.tw/)
- [模板 GitHub](https://github.com/coldwufish/NYCU-thesis-template)
- [LaTeX Workshop 文件](https://github.com/James-Yu/LaTeX-Workshop)

---

**最後更新**: 2025-11-02
**模板版本**: 2024.09.04
**Git Branch**: `claude/summarize-content-011CUjCP2EB5QHBCzzRCp392`
**最新 Commit**: 95792d9 修改中文字體為 Mac 相容的 Kaiti TC
