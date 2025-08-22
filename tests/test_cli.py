"""Test cases for the Chronicler CLI."""

import pytest
from click.testing import CliRunner
from pathlib import Path
from unittest.mock import patch, Mock

from src.chronicler.__main__ import cli
from src.chronicler import __version__


class TestVersion:
    """Test version-related functionality."""
    
    def test_version_flag(self):
        """Test that --version flag returns the correct version."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--version'])
        
        assert result.exit_code == 0
        assert __version__ in result.output
        assert "chronicler" in result.output.lower()
    
    def test_version_import(self):
        """Test that version can be imported correctly."""
        # Test that version is a string and follows expected format
        assert isinstance(__version__, str)
        assert len(__version__) > 0
        # Check if it follows semantic versioning pattern (e.g., "2025.0.1")
        parts = __version__.split('.')
        assert len(parts) >= 2  # At least major.minor
        assert all(part.isdigit() for part in parts)  # All parts should be numeric
    
    def test_version_consistency(self):
        """Test that version is consistent across different access methods."""
        from src.chronicler import __version__ as imported_version
        
        # Test CLI version output
        runner = CliRunner()
        result = runner.invoke(cli, ['--version'])
        
        assert imported_version in result.output
        assert result.exit_code == 0


class TestCLIBasics:
    """Test basic CLI functionality."""
    
    def test_help_command(self):
        """Test that help command works."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert "Chronicler" in result.output
        assert "create" in result.output
        assert "list" in result.output
        assert "show" in result.output
    
    def test_verbose_flag(self):
        """Test that verbose flag works."""
        runner = CliRunner()
        # Test verbose with an actual command, not with --help
        result = runner.invoke(cli, ['--verbose', 'list'])
        
        assert result.exit_code == 0
        assert f"Chronicler v{__version__}" in result.output


class TestCommands:
    """Test individual CLI commands."""
    
    def test_create_command_help(self):
        """Test create command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ['create', '--help'])
        
        assert result.exit_code == 0
        assert "Create a new chronicle" in result.output
        assert "NAME" in result.output
        assert "--description" in result.output
    
    def test_list_command_help(self):
        """Test list command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ['list', '--help'])
        
        assert result.exit_code == 0
        assert "List all chronicles" in result.output
        assert "--format" in result.output
        assert "table" in result.output
        assert "json" in result.output
    
    def test_show_command_help(self):
        """Test show command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ['show', '--help'])
        
        assert result.exit_code == 0
        assert "Show details of a chronicle" in result.output
        assert "NAME" in result.output
    
    def test_create_command_basic(self):
        """Test basic create command functionality."""
        runner = CliRunner()
        result = runner.invoke(cli, ['create', 'test-chronicle'])
        
        assert result.exit_code == 0
        assert "Creating chronicle: test-chronicle" in result.output
    
    def test_create_command_with_description(self):
        """Test create command with description."""
        runner = CliRunner()
        result = runner.invoke(cli, ['create', 'test-chronicle', '--description', 'Test description'])
        
        assert result.exit_code == 0
        assert "Creating chronicle: test-chronicle" in result.output
        assert "Description: Test description" in result.output
    
    def test_list_command_basic(self):
        """Test basic list command functionality."""
        runner = CliRunner()
        result = runner.invoke(cli, ['list'])
        
        assert result.exit_code == 0
        assert "Listing chronicles" in result.output
        assert "table" in result.output
    
    def test_list_command_json_format(self):
        """Test list command with JSON format."""
        runner = CliRunner()
        result = runner.invoke(cli, ['list', '--format', 'json'])
        
        assert result.exit_code == 0
        assert "Listing chronicles" in result.output
        assert "json" in result.output
    
    def test_show_command_basic(self):
        """Test basic show command functionality."""
        runner = CliRunner()
        result = runner.invoke(cli, ['show', 'test-chronicle'])
        
        assert result.exit_code == 0
        assert "Showing chronicle: test-chronicle" in result.output


class TestDocxCommands:
    """Test DOCX-related CLI commands."""
    
    def test_docx_props_command_help(self):
        """Test docx-props command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ['docx-props', '--help'])
        
        assert result.exit_code == 0
        assert "Read document properties" in result.output
        assert "--format" in result.output
        assert "--variables-only" in result.output
    
    def test_docx_vars_command_help(self):
        """Test docx-vars command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ['docx-vars', '--help'])
        
        assert result.exit_code == 0
        assert "Read custom variables" in result.output
        assert "--names-only" in result.output
        assert "--format" in result.output
    
    @patch('src.chronicler.__main__.DocxPropertiesReader')
    def test_docx_props_command_table_format(self, mock_reader_class, tmp_path):
        """Test docx-props command with table format."""
        # Create a temporary .docx file
        docx_file = tmp_path / "test.docx"
        docx_file.write_text("dummy content")
        
        # Mock the reader
        mock_reader = Mock()
        mock_props = Mock()
        mock_props.title = "Test Title"
        mock_props.author = "Test Author"
        mock_props.custom_properties = {"var1": "value1"}
        mock_reader.read_properties.return_value = mock_props
        mock_reader_class.return_value = mock_reader
        
        runner = CliRunner()
        result = runner.invoke(cli, ['docx-props', str(docx_file)])
        
        assert result.exit_code == 0
        mock_reader_class.assert_called_once_with(docx_file)
        mock_reader.read_properties.assert_called_once()
    
    @patch('src.chronicler.__main__.DocxPropertiesReader')
    def test_docx_props_command_json_format(self, mock_reader_class, tmp_path):
        """Test docx-props command with JSON format."""
        # Create a temporary .docx file
        docx_file = tmp_path / "test.docx"
        docx_file.write_text("dummy content")
        
        # Mock the reader
        mock_reader = Mock()
        mock_reader.get_all_properties_dict.return_value = {
            "title": "Test Title",
            "author": "Test Author",
            "custom_var1": "value1"
        }
        mock_reader_class.return_value = mock_reader
        
        runner = CliRunner()
        result = runner.invoke(cli, ['docx-props', str(docx_file), '--format', 'json'])
        
        assert result.exit_code == 0
        assert '"title": "Test Title"' in result.output
        assert '"author": "Test Author"' in result.output
        mock_reader_class.assert_called_once_with(docx_file)
    
    @patch('src.chronicler.__main__.DocxPropertiesReader')
    def test_docx_props_command_variables_only(self, mock_reader_class, tmp_path):
        """Test docx-props command with variables-only flag."""
        # Create a temporary .docx file
        docx_file = tmp_path / "test.docx"
        docx_file.write_text("dummy content")
        
        # Mock the reader
        mock_reader = Mock()
        mock_props = Mock()
        mock_props.custom_properties = {"var1": "value1", "var2": 42}
        mock_reader.read_properties.return_value = mock_props
        mock_reader_class.return_value = mock_reader
        
        runner = CliRunner()
        result = runner.invoke(cli, ['docx-props', str(docx_file), '--variables-only'])
        
        assert result.exit_code == 0
        mock_reader_class.assert_called_once_with(docx_file)
        mock_reader.read_properties.assert_called_once()
    
    @patch('src.chronicler.__main__.DocxPropertiesReader')
    def test_docx_vars_command_basic(self, mock_reader_class, tmp_path):
        """Test docx-vars command basic functionality."""
        # Create a temporary .docx file
        docx_file = tmp_path / "test.docx"
        docx_file.write_text("dummy content")
        
        # Mock the reader
        mock_reader = Mock()
        mock_reader.get_variable_values.return_value = {"var1": "value1", "var2": 42}
        mock_reader_class.return_value = mock_reader
        
        runner = CliRunner()
        result = runner.invoke(cli, ['docx-vars', str(docx_file)])
        
        assert result.exit_code == 0
        assert "var1: value1" in result.output
        assert "var2: 42" in result.output
        mock_reader_class.assert_called_once_with(docx_file)
    
    @patch('src.chronicler.__main__.DocxPropertiesReader')
    def test_docx_vars_command_names_only(self, mock_reader_class, tmp_path):
        """Test docx-vars command with names-only flag."""
        # Create a temporary .docx file
        docx_file = tmp_path / "test.docx"
        docx_file.write_text("dummy content")
        
        # Mock the reader
        mock_reader = Mock()
        mock_reader.get_variable_names.return_value = ["var1", "var2"]
        mock_reader_class.return_value = mock_reader
        
        runner = CliRunner()
        result = runner.invoke(cli, ['docx-vars', str(docx_file), '--names-only'])
        
        assert result.exit_code == 0
        assert "var1" in result.output
        assert "var2" in result.output
        mock_reader_class.assert_called_once_with(docx_file)
        mock_reader.get_variable_names.assert_called_once()
    
    @patch('src.chronicler.__main__.DocxPropertiesReader')
    def test_docx_vars_command_json_format(self, mock_reader_class, tmp_path):
        """Test docx-vars command with JSON format."""
        # Create a temporary .docx file
        docx_file = tmp_path / "test.docx"
        docx_file.write_text("dummy content")
        
        # Mock the reader
        mock_reader = Mock()
        mock_reader.get_variable_values.return_value = {"var1": "value1", "var2": 42}
        mock_reader_class.return_value = mock_reader
        
        runner = CliRunner()
        result = runner.invoke(cli, ['docx-vars', str(docx_file), '--format', 'json'])
        
        assert result.exit_code == 0
        assert '"var1": "value1"' in result.output
        assert '"var2": 42' in result.output
        mock_reader_class.assert_called_once_with(docx_file)
    
    def test_docx_props_nonexistent_file(self):
        """Test docx-props command with non-existent file."""
        runner = CliRunner()
        result = runner.invoke(cli, ['docx-props', 'nonexistent.docx'])
        
        assert result.exit_code != 0
        # Click should handle the file existence check
    
    def test_docx_vars_nonexistent_file(self):
        """Test docx-vars command with non-existent file."""
        runner = CliRunner()
        result = runner.invoke(cli, ['docx-vars', 'nonexistent.docx'])
        
        assert result.exit_code != 0
        # Click should handle the file existence check
