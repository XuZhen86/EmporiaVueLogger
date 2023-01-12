import setuptools

setuptools.setup(
    name='EmporiaVueLogger',
    version='0.1',
    author='XuZhen86',
    url='https://github.com/XuZhen86/EmporiaVueLogger',
    packages=setuptools.find_packages(),
    python_requires='>=3.11',
    install_requires=[
        'absl-py>=1.3.0',
        'esphome>=2022.12.3',
        'paho-mqtt>=1.6.1',
        'line_protocol_cache@git+https://github.com/XuZhen86/LineProtocolCache',
    ],
    entry_points={
        'console_scripts': [
            'emporia-vue-logger-collect-records = emporia_vue_logger.collectrecords:main',
        ],
    },
)
