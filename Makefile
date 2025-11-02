# Makefile for NYCU Thesis Template
# 適用於新版陽明交大論文模板

.PHONY: all clean view help

# 主要編譯目標
MAIN = main
TEX = xelatex
BIB = bibtex

# 預設目標：編譯論文
all: $(MAIN).pdf

# 完整編譯流程 (xelatex -> bibtex -> xelatex -> xelatex)
$(MAIN).pdf: $(MAIN).tex
	@echo "==> 第一次編譯 (xelatex)..."
	$(TEX) -interaction=nonstopmode $(MAIN).tex
	@echo "==> 處理參考文獻 (bibtex)..."
	-$(BIB) $(MAIN)
	@echo "==> 第二次編譯 (xelatex)..."
	$(TEX) -interaction=nonstopmode $(MAIN).tex
	@echo "==> 第三次編譯 (xelatex)..."
	$(TEX) -interaction=nonstopmode $(MAIN).tex
	@echo "==> 編譯完成！"

# 快速編譯 (只執行一次 xelatex)
quick:
	@echo "==> 快速編譯..."
	$(TEX) -interaction=nonstopmode $(MAIN).tex

# 清理中間檔案
clean:
	@echo "==> 清理中間檔案..."
	rm -f *.aux *.bbl *.blg *.log *.out *.toc *.lof *.lot
	rm -f *.fdb_latexmk *.fls *.synctex.gz *.xdv
	rm -f Sections/*.aux
	@echo "==> 清理完成！"

# 完全清理 (包含 PDF)
distclean: clean
	@echo "==> 刪除 PDF..."
	rm -f $(MAIN).pdf
	@echo "==> 完全清理完成！"

# 查看 PDF (Mac)
view: $(MAIN).pdf
	@echo "==> 開啟 PDF..."
	open $(MAIN).pdf

# 顯示幫助訊息
help:
	@echo "可用的指令："
	@echo "  make          - 完整編譯論文"
	@echo "  make quick    - 快速編譯 (只執行一次)"
	@echo "  make clean    - 清理中間檔案"
	@echo "  make distclean- 完全清理 (包含 PDF)"
	@echo "  make view     - 開啟 PDF"
	@echo "  make help     - 顯示此幫助訊息"
