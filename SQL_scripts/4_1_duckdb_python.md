# Install pyenv on WSL
**Install pyenv**
```
curl -fsSL https://pyenv.run | bash
```

**Add this to your bash path by editing ~/.bashrc and add:**
```
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
```

**Install python version and create the environment**
```
pyenv install 3.11.6
pyenv virtualenv 3.11.6 motherduck
```

**Activate the environment**
```
pyenv activate motherduck
```

**Install duckdb**
```
pip install --upgrade pip
pip install duckdb

```

**Test if the motherduck package works**
```python
python -c "import duckdb; print(duckdb.__version__)"
```

**Delete pyenv motherduck environment**
```
pyenv uninstall motherduck
```