from setuptools import find_packages, setup


install_requires = ["Django>=2.2"]

testing_extras = [
    "coverage>=3.7.0",
    "django-debug-toolbar>=3.2,<4",
    "jinja2",
]

docs_extras = [
    "mkdocs>=0.17",
    "mkdocs-rtd-dropdown>=0.0.11",
    "pymdown-extensions>=4.11",
]

setup(
    name="django-influx",
    url="https://github.com/3gi5hi/django-influx",
    project_urls={
        "Changelog": "",
        "Documentation": "",
    },
    author="3gi5hi",
    author_email="egishij@gmail.com",
    description="Influx ORM for the Django Project",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    license="MIT",
    version="1.0.0",
    include_package_data=True,
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=install_requires,
    extras_require={"testing": testing_extras, "docs": docs_extras},
    classifiers=[
        "Framework :: Django",
        "Framework :: Django :: 2.2",
        "Framework :: Django :: 3.0",
        "Framework :: Django :: 3.1",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.0",
        "Framework :: Django :: 4.1",
        "Framework :: Django :: 4.2",
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
)
