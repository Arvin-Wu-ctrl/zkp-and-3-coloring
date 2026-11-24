import json
import pytest
from pathlib import Path

import src.run as run

TEST_CORRUPTED = "tests/test_run_corrupted.json"
TEST_SOURCE = "tests/test_run_source.json"
TEST_GENERATE = "tests/test_run_generate.json"

def _patch_argv(monkeypatch, config_path: str):
	monkeypatch.setattr(run, "argv", [run.argv[0], config_path])

def _get_ouput_path(config_path: str) -> Path:
	with open(config_path, 'r') as file:
		return Path(json.load(file)["output"])

def test_run_respect_output_parameter(monkeypatch):
	output_path = _get_ouput_path(TEST_CORRUPTED)
	if output_path.is_file():
		last_modified = output_path.stat().st_mtime
	else:
		last_modified = 0

	_patch_argv(monkeypatch, TEST_CORRUPTED)
	run.main()

	assert last_modified != output_path.stat().st_mtime

def test_run_result_reproducible(monkeypatch):
	_patch_argv(monkeypatch, TEST_CORRUPTED)
	output_path = _get_ouput_path(TEST_CORRUPTED)

	run.main()
	with open(output_path, 'r') as file:
		result = file.read()
	run.main()
	with open(output_path, 'r') as file:
		assert result == file.read()

def test_run_result_contains_graphs_from_source(monkeypatch):
	_patch_argv(monkeypatch, TEST_SOURCE)
	with open(TEST_SOURCE, 'r') as file:
		config = json.load(file)
		output_path = config["output"]
		graph = config["graphs"][list(config["graphs"].keys())[0]]
		source_path = graph["source"]
		coloring_path = graph["coloring"]

	run.main()

	with open(output_path, 'r') as file:
		result = file.read()
		assert source_path in result
		assert coloring_path in result

def test_run_result_contains_generated_graphs(monkeypatch):
	_patch_argv(monkeypatch, TEST_GENERATE)
	output_path = _get_ouput_path(TEST_GENERATE)

	run.main()

	with open(output_path, 'r') as file:
		graphs = json.load(file)["graphs"]
		assert len(graphs) > 0

@pytest.mark.parametrize(
	"path",
	[
		TEST_CORRUPTED,
		TEST_GENERATE,
		TEST_SOURCE,
	])
def test_run_result_contains_graph_info(monkeypatch, path):
	_patch_argv(monkeypatch, path)
	output_path = _get_ouput_path(path)

	run.main()

	with open(output_path, 'r') as file:
		graphs = json.load(file)["graphs"]
		for graph in graphs.values():
			assert "nodes" in graph
			assert "edges" in graph
			assert "bad_edges" in graph

@pytest.mark.parametrize(
	"path",
	[
		TEST_CORRUPTED,
		TEST_GENERATE,
		TEST_SOURCE,
	])
def test_run_result_contains_graph_statistics(monkeypatch, path):
	_patch_argv(monkeypatch, path)
	output_path = _get_ouput_path(path)

	run.main()

	with open(output_path, 'r') as file:
		graphs = json.load(file)["graphs"]
		for graph in graphs.values():
			assert 0 <= graph["acceptance"] <= 1
			assert 0 <= graph["theoretical_acceptance"] <= 1

@pytest.mark.parametrize(
	"path",
	[
		TEST_CORRUPTED,
		TEST_GENERATE,
		TEST_SOURCE,
	])
def test_run_result_contains_session_result(monkeypatch, path):
	_patch_argv(monkeypatch, path)
	output_path = _get_ouput_path(path)

	run.main()

	with open(output_path, 'r') as file:
		sessions = json.load(file)["sessions"]
		assert len(sessions) > 0
		for session in sessions.values():
			assert "accepted" in session
			assert "rounds" in session
