// 1. O‘zbekcha matnlar
const translations = {
  loading: "Yuklanmoqda...",
  cityNotFound: "Shahar topilmadi",
  networkError: "Tarmoq xatosi",
  locationError: "Joylashuv aniqlanmadi",
  loadingLocation: "Joylashuvingiz aniqlanmoqda..."
};

// 2. API sozlamalari
const API_KEY = '376dd1241efcc4f7a4597cbe893cca72';
const CURRENT_URL = 'https://api.openweathermap.org/data/2.5/weather';
const ONE_CALL_URL = 'https://api.openweathermap.org/data/2.5/onecall';
const LONG_FORECAST_URL = 'https://api.open-meteo.com/v1/forecast';

// 3. Global o‘zgaruvchilar
let currentCityCoords = {};

// 4. DOM elementlari
const cityInput = document.getElementById('cityInput');
const searchBtn = document.getElementById('searchBtn');
const locationBtn = document.getElementById('locationBtn');
const loading = document.getElementById('loading');
const weatherInfo = document.getElementById('weatherInfo');
const error = document.getElementById('error');
const errorText = document.getElementById('errorText');
const forecastPanel = document.getElementById('forecastPanel');

// 5. Yordamchi funksiyalar
function hideAll() {
  weatherInfo.style.display = 'none';
  error.style.display = 'none';
  loading.style.display = 'none';
}
function showError(msg) {
  hideAll(); error.style.display = 'flex'; errorText.textContent = msg;
}
function showLoading(msg) {
  hideAll(); loading.style.display = 'block'; loading.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${msg}`;
}

// 6. Asosiy ob-havo (current)
async function fetchWeather(city) {
  try {
    showLoading(translations.loading);
    const res = await fetch(`${CURRENT_URL}?q=${city}&appid=${API_KEY}&units=metric&lang=uz`);
    if (!res.ok) throw new Error(translations.cityNotFound);
    const data = await res.json();
    displayCurrentWeather(data);
    saveCoords(data.coord.lat, data.coord.lon);
    loadForecast('daily');
  } catch (err) {
    showError(err.message === translations.cityNotFound ? translations.cityNotFound : translations.networkError);
  }
}
function displayCurrentWeather(data) {
  hideAll(); weatherInfo.style.display = 'block';
  document.getElementById('cityName').textContent = `${data.name}, ${data.sys.country}`;
  document.getElementById('date').textContent = new Date().toLocaleString('uz-UZ');
  document.getElementById('temp').textContent = `${Math.round(data.main.temp)}°C`;
  document.getElementById('weatherDesc').textContent = data.weather[0].description;
  document.getElementById('feelsLike').textContent = `His qilinadi: ${Math.round(data.main.feels_like)}°C`;
  document.getElementById('weatherIcon').src = `https://openweathermap.org/img/wn/${data.weather[0].icon}@4x.png`;
  document.getElementById('visibility').textContent = `${(data.visibility / 1000).toFixed(1)} km`;
  document.getElementById('humidity').textContent = `${data.main.humidity}%`;
  document.getElementById('windSpeed').textContent = `${data.wind.speed} m/s`;
  document.getElementById('pressure').textContent = `${data.main.pressure} hPa`;
  const sunrise = new Date(data.sys.sunrise * 1000).toLocaleTimeString('uz-UZ');
  const sunset = new Date(data.sys.sunset * 1000).toLocaleTimeString('uz-UZ');
  document.getElementById('sunrise').textContent = `Quyosh chiqishi: ${sunrise}`;
  document.getElementById('sunset').textContent = `Quyosh botishi: ${sunset}`;
}

// 7. Geolokatsiya
function getCurrentLocation() {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(pos => {
      const {latitude: lat, longitude: lon} = pos.coords;
      fetchWeatherByCoords(lat, lon);
    }, () => showError(translations.locationError));
  } else showError("Brauzer geolokatsiyani qo‘llab-quvvatlamaydi");
}
async function fetchWeatherByCoords(lat, lon) {
  try {
    showLoading(translations.loadingLocation);
    const res = await fetch(`${CURRENT_URL}?lat=${lat}&lon=${lon}&appid=${API_KEY}&units=metric&lang=uz`);
    if (!res.ok) throw new Error(translations.cityNotFound);
    const data = await res.json();
    displayCurrentWeather(data);
    saveCoords(lat, lon);
    loadForecast('daily');
  } catch (err) { showError(err.message); }
}
function saveCoords(lat, lon) { currentCityCoords = {lat, lon}; }

// 8. Bashorat tizimi (kunlik, 7, 10, 15)
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', e => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    e.target.classList.add('active');
    loadForecast(e.target.dataset.range);
  });
});
async function loadForecast(range) {
  if (!currentCityCoords.lat) { console.warn('❌ coords empty'); return; }
  const {lat, lon} = currentCityCoords;
  const days = range === 'daily' ? 1 : (range === '7days' ? 7 : (range === '10days' ? 10 : 15));

  try {
    const res = await fetch(
      `${LONG_FORECAST_URL}?latitude=${lat}&longitude=${lon}&daily=weathercode,temperature_2m_max,temperature_2m_min&timezone=auto&forecast_days=${days}`
    );
    if (!res.ok) throw new Error('Bashorat topilmadi');
    const data = await res.json();
    renderLongForecast(data.daily, days);
  } catch (err) {
    forecastPanel.innerHTML = `<p class="error">${err.message}</p>`;
  }
}
function renderLongForecast(daily, days) {
  forecastPanel.innerHTML = '';
  const dayNames = ['Yak','Dush','Sesh','Chor','Pay','Jum','Shan'];
  for (let i = 0; i < days; i++) {
    const date = new Date(daily.time[i]);
    const icon = getOpenMeteoIcon(daily.weathercode[i]);
    const name = i === 0 ? 'Bugun' : dayNames[date.getDay()];
    const dateStr = formatDate(date);
    forecastPanel.insertAdjacentHTML('beforeend', `
      <div class="forecast-card">
        <div class="day">${name}</div>
        <small>${dateStr}</small>
        <img src="${icon}" alt="">
        <div class="temp">${Math.round(daily.temperature_2m_max[i])}°/${Math.round(daily.temperature_2m_min[i])}°</div>
      </div>
    `);
  }
}

// 9. 10-15 kunlik → Open-Meteo
async function loadLongForecast(days) {
  const {lat, lon} = currentCityCoords;
  try {
    const res = await fetch(`${LONG_FORECAST_URL}?latitude=${lat}&longitude=${lon}&daily=weathercode,temperature_2m_max,temperature_2m_min&timezone=auto&forecast_days=${days}`);
    if (!res.ok) throw new Error('Uzoq bashorat topilmadi');
    const data = await res.json();
    renderLongForecast(data.daily, days);
  } catch (err) {
    forecastPanel.innerHTML = `<p class="error">${err.message}</p>`;
  }
}
function getOpenMeteoIcon(code) {
  if (code === 0) return 'https://openweathermap.org/img/wn/01d@2x.png';
  if (code <= 2) return 'https://openweathermap.org/img/wn/02d@2x.png';
  if (code <= 5) return 'https://openweathermap.org/img/wn/04d@2x.png';
  if (code <= 67) return 'https://openweathermap.org/img/wn/09d@2x.png';
  if (code <= 77) return 'https://openweathermap.org/img/wn/13d@2x.png';
  return 'https://openweathermap.org/img/wn/11d@2x.png';
}

// 10. Tugma & Enter
searchBtn.addEventListener('click', () => {
  const city = cityInput.value.trim(); if (city) fetchWeather(city);
});
cityInput.addEventListener('keypress', e => {
  if (e.key === 'Enter') { const city = cityInput.value.trim(); if (city) fetchWeather(city); }
});
locationBtn.addEventListener('click', getCurrentLocation);

// 11. Birinchi ochilishi (standart)
window.addEventListener('DOMContentLoaded', () => fetchWeather('Toshkent'));

// === Hafta kunlari va sana ===
const days = ['Ya', 'Du', 'Se', 'Chor', 'Pay', 'Ju', 'Shan'];
const months = ['Yan', 'Fev', 'Mar', 'Apr', 'May', 'Iyn', 'Iyl', 'Avg', 'Sen', 'Okt', 'Noy', 'Dek'];

function formatDate(date) {
  const d = date.getDate();
  const m = months[date.getMonth()];
  return `${d} ${m}`;
}

// Hafta kunlari kartalariga sana qo‘shish
document.querySelectorAll('.forecast-card .day').forEach((el, idx) => {
  const date = new Date();
  date.setDate(date.getDate() + idx);
  el.insertAdjacentHTML('afterend', `<small>${formatDate(date)}</small>`);
});