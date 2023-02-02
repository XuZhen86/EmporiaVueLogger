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
        'aioesphomeapi>=13.0.0',
        'esphome>=2022.12.3',
        'line_protocol_cache@git+https://github.com/XuZhen86/LineProtocolCache@26ade43329fd143fd2311926620e5a01082be1e1',
    ],
    entry_points={
        'console_scripts': [
            'emporia-vue-logger-collect-records = emporia_vue_logger.collectrecords:main',
        ],
    },
)
