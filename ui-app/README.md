
# Generar la Imagen del Contenedor

```sh
docker buildx build --progress=plain . -t comsatel/iallm:0.1.0
```

# Instalacion de enorno local

```sh
python3.9 -m venv /opt/llm2
/opt/llm2/bin/python3.9 -m pip install --upgrade pip
```

```sh
python3.9 -m ensurepip --upgradepython -m ensurepip --upgrade
```

```sh
/opt/llm2/bin/python3.9 -m pip install -r requirements.txt
```

# Prompts ejemplos

```text
Generar una gráfica comparativa de la capacidad de memoria de los modelos de GPU de NVIDIA.
```
