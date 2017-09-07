import dlen.dlen as dlen


def test_blank_console():
    """Test blank in command line."""
    assert dlen.main() is None


def test_blank():
    """Test blank."""
    assert dlen.DefLen(files_content=['']).show_console is False


def test_good_def():
    """Test good def."""
    test_input = [(
        'def demo_good_test():\n'
        '    # line1\n'
        '    # line2\n'
        '    # line3\n'
        '    # line4\n\n\n')]
    test_input.append(test_input[0])
    result = dlen.DefLen(files_content=test_input)
    assert result.show_console is False
    assert result.output == []


def test_error_def():
    """Test error def."""
    test_input = [(
        'def demo_error_test():\n'
        '    # line1\n'
        '    # line2\n'
        '    # line3\n' +
        '    # lineN\n' * 20 +
        '\n\n\n')]
    test_input.append(test_input[0])
    result = dlen.DefLen(files_content=test_input)
    assert result.show_console is False
    assert result.output == [
        '[ERROR] demo_error_test function too long (23 > 20 lines)',
        '[ERROR] demo_error_test function too long (23 > 20 lines)']


def test_warn_def():
    """Test warn def."""
    reload(dlen)
    test_input = [(
        'def demo_warn_test():\n'
        '    # line1\n'
        '    # line2\n'
        '    # line3\n' +
        '    # lineN\n' * 10 +
        '\n\n\n')]
    result = dlen.DefLen(files_content=test_input)
    assert result.show_console is False
    assert result.output == [
        '[WARN] demo_warn_test function too long (13 > 12 lines)']


def test_error_deftab():
    """Test detect fake tab."""
    reload(dlen)
    test_input = [(
        'def demo_warn_test():\n'
        '    # line1\n'
        '    # line2\n'
        '# line3\n' +
        '    # lineN\n' * 10 +
        '\n\n\n')]
    result = dlen.DefLen(files_content=test_input)
    assert result.show_console is False
    assert result.output == []


def test_good_class():
    """Test godd class."""
    reload(dlen)
    test_input = [(
        'class DemoGoodClass():\n'
        '    # line1\n'
        '    # line2\n'
        '    # line3\n' +
        '    # lineN\n' * 100 +
        '\n\n\n')]
    result = dlen.DefLen(files_content=test_input)
    assert result.show_console is False
    assert result.output == []


def test_error_class():
    """Test error class."""
    reload(dlen)
    test_input = [(
        'class DemoGoodClass():\n    # line1\n    # line2\n' +
        '    # lineN\n' * 1000 +
        '\n\n\n')]
    test_input.append(test_input[0])
    result = dlen.DefLen(files_content=test_input)
    assert result.show_console is False
    assert result.output == [
        '[ERROR] DemoGoodClass class too long (1002 > 500 lines)',
        '[ERROR] DemoGoodClass class too long (1002 > 500 lines)']


GOOD = 0
for f in ['test_blank_console',
          'test_blank',
          'test_good_def',
          'test_error_def',
          'test_error_deftab',
          'test_warn_def',
          'test_good_class',
          'test_error_class']:
    globals()[f]()
    GOOD += 1
print('GOOD {} test'.format(GOOD))
