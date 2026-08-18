.PHONY: sync build verify check reproduce specimen

sync:
	uv sync --frozen

build:
	uv run python font-lab/build_ultra_tabular.py

verify:
	uv run python font-lab/build_ultra_tabular.py --verify-only

check:
	uv run python -m compileall -q font-lab
	$(MAKE) verify

reproduce:
	$(MAKE) build
	git diff --exit-code -- fonts/

specimen:
	python3 -m http.server 5310 --directory .
