from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="sanatan-sdk",
    version="0.7.1",
    author="Sanatan Learnings",
    author_email="arun.gupta@gmail.com",
    description="SDK for generating rich multimedia content for verse-based texts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sanatan-learnings/sanatan-sdk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "openai>=1.0.0",
        "elevenlabs>=1.0.0",
        "requests>=2.31.0",
        "Pillow>=10.0.0",
        "python-dotenv>=1.0.0",
        "PyYAML>=6.0.0",
        "sentence-transformers>=2.2.0",
        "torch>=2.0.0",
        "beautifulsoup4>=4.12.0",
    ],
    entry_points={
        'console_scripts': [
            'verse-generate=verse_sdk.cli.generate:main',
            'verse-embeddings=verse_sdk.embeddings.generate_embeddings:main',
            'verse-audio=verse_sdk.audio.generate_audio:main',
            'verse-images=verse_sdk.images.generate_theme_images:main',
            'verse-deploy=verse_sdk.deployment.deploy:main',
            'verse-fetch-text=verse_sdk.fetch.fetch_verse_text:main',
            'verse-status=verse_sdk.cli.status:main',
            'verse-sync=verse_sdk.cli.sync:main',
        ],
    },
)
