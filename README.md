<!-- PROJECT SHIELDS -->
<div align="center">
  
  [![Contributors][contributors-shield]][contributors-url]
  [![Forks][forks-shield]][forks-url]
  [![Stargazers][stars-shield]][stars-url]
  [![Issues][issues-shield]][issues-url]
  [![Unlicense License][license-shield]][license-url]
  [![LinkedIn][linkedin-shield]][linkedin-url]
  
</div>


<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/meteostat/meteostat-python">
    <img src="https://media.meteostat.net/icon.svg" alt="Meteostat Logo" width="80" height="80">
  </a>

  <h3 align="center">Meteostat Python Package</h3>

  <p align="center">
    Access and analyze historical weather and climate data with Python.
    <p>
      <a href="https://dev.meteostat.net"><strong>Explore the docs »</strong></a>
    </p>
    <p>
      <a href="https://meteostat.net">Visit Website</a>
      &middot;
      <a href="https://github.com/othneildrew/Best-README-Template/issues/new?labels=bug&template=bug-report---.md">Report Bug</a>
      &middot;
      <a href="https://github.com/othneildrew/Best-README-Template/issues/new?labels=enhancement&template=feature-request---.md">Request Feature</a>
    </p>
  </p>
</div>

## 📚 Installation

The Meteostat Python package is available through [PyPI](https://pypi.org/project/meteostat/):

```sh
pip install meteostat
```

## 🚀 Usage

Let's plot 2018 temperature data for Frankfurt, Germany:

```python
from datetime import date
import matplotlib.pyplot as plt
import meteostat as ms

# Specify location and time range
POINT = ms.Point(50.1155, 8.6842, 113)  # Try with your location
START = date(2018, 1, 1)
END = date(2018, 12, 31)

# Get nearby weather stations
stations = ms.stations.nearby(POINT, limit=4)

# Get daily data & perform interpolation
ts = ms.daily(stations, START, END)
df = ms.interpolate(ts, POINT)

# Plot line chart including average, minimum and maximum temperature
df.plot(y=[ms.Parameter.TEMP, ms.Parameter.TMIN, ms.Parameter.TMAX])
plt.show()
```

Take a look at the expected output:

![2018 temperature data for Frankfurt, Germany][product-screenshot]

## 🤝 Contributing

Please read our [contributing guidelines](https://dev.meteostat.net/python/contributing) for details on how to contribute to the Meteostat Python library.

**Top contributors**

<a href="https://github.com/meteostat/meteostat-python/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=meteostat/meteostat-python" alt="Meteostat Contributors" />
</a>

## 🌟 Featured In

Meteostat has been featured and used by various media outlets and organizations, including:

- [Towards Data Science](https://towardsdatascience.com/get-temperature-data-by-location-with-python-52ed872dd621/)
- [ZEIT ONLINE](https://www.zeit.de/digital/internet/2022-03/desinformation-russland-ukraine-fotos-fake-news-falschinformation-echtheit)
- [Deutsche Presse-Agentur (dpa)](https://dpa-factchecking.com/germany/230103-99-92282/)
- [heise online](https://www.heise.de/news/Open-Source-Projekt-zu-Klimadaten-Meteostat-Python-Library-1-0-erschienen-4985015.html)

Join the growing community of users and researchers relying on Meteostat for their weather data needs.

## 📄 License

Meteostat is licensed under the **MIT License**. Data provided by Meteostat is generally licensed under the [**Creative Commons Attribution 4.0 International (CC BY 4.0)**](https://creativecommons.org/licenses/by/4.0) license. Please refer to the [documentation](https://dev.meteostat.net/license) for more information.


<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/meteostat/meteostat-python.svg?style=for-the-badge
[contributors-url]: https://github.com/meteostat/meteostat-python/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/meteostat/meteostat-python.svg?style=for-the-badge
[forks-url]: https://github.com/meteostat/meteostat-python/network/members
[stars-shield]: https://img.shields.io/github/stars/meteostat/meteostat-python.svg?style=for-the-badge
[stars-url]: https://github.com/meteostat/meteostat-python/stargazers
[issues-shield]: https://img.shields.io/github/issues/meteostat/meteostat-python.svg?style=for-the-badge
[issues-url]: https://github.com/meteostat/meteostat-python/issues
[license-shield]: https://img.shields.io/github/license/meteostat/meteostat-python.svg?style=for-the-badge
[license-url]: https://github.com/meteostat/meteostat-python/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://www.linkedin.com/company/meteostat
[product-screenshot]: https://dev.meteostat.net/assets/img/py-example-chart.046f8b8e.png
