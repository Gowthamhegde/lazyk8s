from setuptools import setup

setup(
    name="lazyk8s",
    version="1.0.0",
    description="A stylish terminal UI for Kubernetes",
    py_modules=["lazykube"],
    install_requires=[
        "textual>=0.50.0",
        "kubernetes>=28.0.0",
    ],
    entry_points={
        "console_scripts": [
            "lazyk8s=lazykube:main",
        ],
    },
    python_requires=">=3.9",
)
