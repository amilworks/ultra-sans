.PHONY: sync build verify check reproduce specimen hero proof

sync:
	uv sync --frozen

build:
	uv run python font-lab/build_ultra_tabular.py

verify:
	uv run python font-lab/build_ultra_tabular.py --verify-only

check:
	uv run python -m compileall -q font-lab
	uv run python -m unittest discover -s font-lab -p 'test_*.py' -v
	uv run python font-lab/render_readme_hero.py --verify-only
	$(MAKE) verify

reproduce:
	$(MAKE) build
	git diff --exit-code -- fonts/

specimen:
	python3 -m http.server 5310 --directory .

hero:
	uv run python font-lab/render_readme_hero.py

proof:
	uv run python font-lab/build_circular_proof.py

proof-0102:
	uv run python font-lab/build_refinement_proof.py
