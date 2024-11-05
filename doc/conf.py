# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import datetime as dt

import lori

project = "Lori"
author = "ISC Konstanz e.V."

copyright = f"{dt.datetime.now().year}, ISC Konstanz e.V"

# The full project version, used as the replacement for |release| and e.g. in the HTML templates.
# For example, for the Python documentation, this may be something like 1.0.0rc1.
release = "%s" % lori.__version__

# The major project version, used as the replacement for |version|.
# For example, for the Python documentation, this may be something like 1.0.
version = ".".join(release.split(".")[:2])

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named "sphinx.ext.*") or your custom
# ones.
extensions = [
    "autoapi",  # API documentation support
    "myst_parser",  # Markdown support
    "sphinx.ext.napoleon",
    "sphinx.ext.inheritance_diagram",
    "sphinx.ext.viewcode",
]

# The suffix of source filenames.
source_suffix = {
    ".md": "markdown",
    ".rst": "restructuredtext",
}
# The encoding of source files.
# source_encoding = "utf-8-sig"

# A list of paths that contain extra templates (or templates that overwrite
# builtin/theme-specific templates). Relative paths are taken as relative to
# the configuration directory.
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
# language = None

# True to include special members (like __configure__) with docstrings in the documentation.
napoleon_include_special_with_doc = True

suppress_warnings = ["autoapi.python_import_resolution"]


# -- AutoAPI Configuration -------------------------------------------------
# https://sphinx-autoapi.readthedocs.io/en/latest/reference/config.html#customisation-options

autoapi_dirs = ["../lori"]

autoapi_ignore = [
    "*tests/*",
    "*tests.py",
    "*validation.py",
    "*version.py",
    "*.rst",
    "*.yml",
    "*.yaml",
    "*.toml",
    "*.md",
    "*.json",
]

autoapi_options = [
    "members",
    "private-members",
    "special-members",
    # 'undoc-members',
    "show-inheritance",
    "show-inheritance-diagram",
    "show-module-summary",
]

autoapi_python_class_content = "both"
autoapi_member_order = "groupwise"
autoapi_root = "code"
autoapi_keep_files = False


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
# html_theme = "alabaster"
html_theme = "pydata_sphinx_theme"

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
# https://pydata-sphinx-theme.rtfd.io/en/latest/user_guide/configuring.html
html_theme_options = {
    "github_url": "https://github.com/isc-konstanz/lori",
    "icon_links": [
        {
            "name": "PyPI",
            "url": "https://pypi.org/project/lori/",
            "icon": "fab fa-python",
        },
    ],
    "use_edit_page_button": True,
    "show_toc_level": 1,
    "navbar_persistent": ["theme-switcher"],
    "navbar_start": ["navbar-logo", "version-switcher"],
    "navbar_end": ["navbar-icon-links.html"],
    "footer_start": ["copyright"],
    "footer_end": ["footer"],
}

html_sidebars = {
    "**": [
        "search-field.html",
        "sidebar-nav-bs.html",
    ],
}

html_context = {
    "github_user": "isc-konstanz",
    "github_repo": "lori",
    "github_version": "stable",
    "default_mode": "light",
    "doc_path": "doc",
}

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
html_logo = "_images/lori-logo.svg"

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
html_favicon = "_images/lori-favicon.ico"

# A list of paths that contain custom static files (such as style sheets or script files).
# Relative paths are taken as relative to the configuration directory.
html_static_path = ["_static"]

# If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
# html_show_copyright = False
