#!/usr/bin/env python3
import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the config functions
from src.config import parse_amqp_url

def test_parse_amqp_url_complete():
    """Test parsing a complete AMQP URL."""
    url = "amqp://user:pass@host:5672/vhost"
    result = parse_amqp_url(url)

    assert result["host"] == "host"
    assert result["port"] == 5672
    assert result["username"] == "user"
    assert result["password"] == "pass"
    assert result["vhost"] == "vhost"
    assert result["use_ssl"] == False

def test_parse_amqp_url_ssl():
    """Test parsing an AMQPS URL."""
    url = "amqps://user:pass@host:5671/vhost"
    result = parse_amqp_url(url)

    assert result["host"] == "host"
    assert result["port"] == 5671
    assert result["username"] == "user"
    assert result["password"] == "pass"
    assert result["vhost"] == "vhost"
    assert result["use_ssl"] == True

def test_parse_amqp_url_no_port():
    """Test parsing a URL without a port."""
    url = "amqp://user:pass@host/vhost"
    result = parse_amqp_url(url)

    assert result["host"] == "host"
    assert result["port"] == 5672  # Default port
    assert result["username"] == "user"
    assert result["password"] == "pass"
    assert result["vhost"] == "vhost"
    assert result["use_ssl"] == False

def test_parse_amqp_url_no_vhost():
    """Test parsing a URL without a vhost."""
    url = "amqp://user:pass@host:5672"
    result = parse_amqp_url(url)

    assert result["host"] == "host"
    assert result["port"] == 5672
    assert result["username"] == "user"
    assert result["password"] == "pass"
    assert result["vhost"] == "/"  # Default vhost
    assert result["use_ssl"] == False

def test_parse_amqp_url_special_chars():
    """Test parsing a URL with special characters."""
    url = "amqp://user:p%40ss@host:5672/vho%2Fst"
    result = parse_amqp_url(url)

    assert result["host"] == "host"
    assert result["port"] == 5672
    assert result["username"] == "user"
    assert result["password"] == "p@ss"
    assert result["vhost"] == "vho/st"
    assert result["use_ssl"] == False
