"""Unit tests for CLI."""

import pytest
from click.testing import CliRunner

from src.cli import cli, main


class TestCLI:
    """Tests for CLI commands."""
    
    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()
    
    def test_cli_help(self, runner):
        """Test CLI help message."""
        result = runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert "YouTube Miner" in result.output
    
    def test_cli_version(self, runner):
        """Test CLI version flag."""
        result = runner.invoke(cli, ['--version'])
        
        assert result.exit_code == 0
        assert "1.0.0" in result.output
    
    def test_models_command(self, runner):
        """Test models listing command."""
        result = runner.invoke(cli, ['models'])
        
        assert result.exit_code == 0
        assert "whisper-tiny" in result.output
        assert "faster-whisper" in result.output
    
    def test_compare_command(self, runner):
        """Test compare command with identical texts."""
        result = runner.invoke(cli, ['compare', 'hello world', 'hello world'])
        
        assert result.exit_code == 0
        assert "WER" in result.output
        assert "0.00%" in result.output  # Perfect match
    
    def test_compare_command_different_texts(self, runner):
        """Test compare command with different texts."""
        result = runner.invoke(cli, ['compare', 'hello world', 'hello there'])
        
        assert result.exit_code == 0
        assert "WER" in result.output
        assert "CER" in result.output
        assert "Semantic Similarity" in result.output
    
    def test_run_command_help(self, runner):
        """Test run command help."""
        result = runner.invoke(cli, ['run', '--help'])
        
        assert result.exit_code == 0
        assert "--model" in result.output
        assert "--output" in result.output
        assert "--verbose" in result.output
    
    def test_download_command_help(self, runner):
        """Test download command help."""
        result = runner.invoke(cli, ['download', '--help'])
        
        assert result.exit_code == 0
        assert "URL" in result.output
    
    def test_chunk_command_help(self, runner):
        """Test chunk command help."""
        result = runner.invoke(cli, ['chunk', '--help'])
        
        assert result.exit_code == 0
        assert "--duration" in result.output
    
    def test_transcribe_command_help(self, runner):
        """Test transcribe command help."""
        result = runner.invoke(cli, ['transcribe', '--help'])
        
        assert result.exit_code == 0
        assert "--model" in result.output
        assert "--language" in result.output
    
    def test_captions_command_help(self, runner):
        """Test captions command help."""
        result = runner.invoke(cli, ['captions', '--help'])
        
        assert result.exit_code == 0
        assert "--language" in result.output
    
    def test_convert_command_help(self, runner):
        """Test convert command help."""
        result = runner.invoke(cli, ['convert', '--help'])
        
        assert result.exit_code == 0
        assert "INPUT_PATH" in result.output


class TestCLIErrorHandling:
    """Tests for CLI error handling."""
    
    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()
    
    def test_run_invalid_url(self, runner, temp_dir):
        """Test run command with invalid URL."""
        result = runner.invoke(cli, [
            'run',
            'https://example.com/invalid',
            '--output', str(temp_dir),
        ])
        
        assert result.exit_code != 0
        assert "Error" in result.output
    
    def test_convert_nonexistent_file(self, runner):
        """Test convert command with non-existent file."""
        result = runner.invoke(cli, ['convert', '/nonexistent/file.wav'])
        
        assert result.exit_code != 0
    
    def test_chunk_nonexistent_file(self, runner):
        """Test chunk command with non-existent file."""
        result = runner.invoke(cli, ['chunk', '/nonexistent/file.wav'])
        
        assert result.exit_code != 0
    
    def test_transcribe_nonexistent_file(self, runner):
        """Test transcribe command with non-existent file."""
        result = runner.invoke(cli, ['transcribe', '/nonexistent/file.wav'])
        
        assert result.exit_code != 0

