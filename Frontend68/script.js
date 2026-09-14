let currentLatitude=23.3441;
let currentLongitude=85.3096;
//Live-date added 
function updateDate(){
    const now=new Date();
    const day=now.toLocaleDateString("en-IN",{
        weekday:"long"
    });

    const date=now.getDate();
    const month=now.toLocaleDateString("en-IN",{
        month:"long"
    }).toUpperCase();

    document.querySelector(".date").textContent=`${day} · ${date} ${month}`;
}
updateDate();
setInterval(updateDate,60000);
// --------------------------------------------------------------------------------------------
// ------------------------------Live-location added-------------------------------------------
// --------------------------------------------------------------------------------------------
const searchBar=document.getElementById("search-bar");
const searchButton=document.querySelector(".search-button");

searchButton.addEventListener("click",async(event) => {
    event.preventDefault();
    const query =searchBar.value.trim();
    
    if(!query) return;
    try{
        const response=await fetch(
            `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(query)}&count=1&language-en&format=json`
        );
        if(!response.ok){
            throw new Error("API error");
        }
        const data=await response.json();

        if(!data.results||data.results.length===0){
            alert("Location not found");
            return;
        }
        const location=data.results[0];
        currentLatitude=location.latitude;
        currentLongitude=location.longitude;
        const city=location.name|| "";
        const state=location.admin1||"";
        const district= 
            location.admin2||
            location.admin3||
            "";

        //Header-> City, State
        document.querySelector(".location-address h3").textContent=[city, state].filter(Boolean).join(", ");

        //Weather Card-> City
        document.querySelector(".location-line1").textContent= city;

        //Weather Card -> District, state
        document.querySelector(".location-line2").textContent=[district, state].filter(Boolean).join(", ");

        //LIVE Weather
        await updateCurrentWeathter(location.latitude, location.longitude);
        await updateFourWeatherBoxes(location.latitude,location.longitude);
    } catch(error){
        console.error(error);
        alert("Unable to fetch location");
    }
});
// ======================================================
// ================= DARK / LIGHT MODE ==================
// ======================================================

const modeButton = document.querySelector(".mode");
const modeIcon = document.querySelector(".mode i");

function applyTheme(theme) {

    if (theme === "dark") {

        document.body.classList.add("dark-mode");

        modeIcon.className = "fa-solid fa-sun";
        modeIcon.style.color = "white";

    } else {

        document.body.classList.remove("dark-mode");

        modeIcon.className = "fa-solid fa-circle-half-stroke";
        modeIcon.style.color = "black";
    }
}

// ======================================================
// Load saved theme after refresh
// ======================================================

const savedTheme = localStorage.getItem("theme") || "light";

applyTheme(savedTheme);

// ======================================================
// Theme button click
// ======================================================

modeButton.addEventListener("click", () => {
    const darkMode =
        document.body.classList.contains("dark-mode");
    const newTheme = darkMode ? "light" : "dark";
    localStorage.setItem("theme", newTheme);
    applyTheme(newTheme);
});
//Refresh k bad bhi selected mode rahega
if(localStorage.getItem("theme") ==="dark"){
    document.boby.classList.add("dark-mode");

    modeIcon.className="fa-solid fa-sun";
    modeIcon.style.color="white";
}
// ===================== Weather Icon Auto Change =====================
const weatherIcon = document.getElementById("weather-icon");
let currentWeatherCode = 2; // default fallback

function getWeatherIconPath(weatherCode) {
    const hour = new Date().getHours();
    const isDay = hour >= 6 && hour < 18;

    const iconMap = {
        0:  { day: "icon/clear-sky-day.png",         night: "icon/clear-sky-night.png" },
        1:  { day: "icon/mainly-clear-day.png",      night: "icon/mainly-clear-night.png" },
        2:  { day: "icon/partly-cloudy-day.png",     night: "icon/partly-cloudy-night.jpeg" },
        3:  { day: "icon/cloudy-day.png",            night: "icon/cloudy-night.png" },
        45: { day: "icon/fog-day.png",               night: "icon/fog-night.png" },
        48: { day: "icon/fog-day.png",               night: "icon/fog-night.png" },

        51: { day: "icon/light-drizzle-day.png",     night: "icon/light-drizzle-night.png" },
        53: { day: "icon/drizzle-day.png",           night: "icon/drizzle-night.png" },
        55: { day: "icon/heavy-drizzle-day.png",     night: "icon/heavy-drizzle-night.png" },

        61: { day: "icon/light-rain-day.png",        night: "icon/light-rain-night.png" },
        63: { day: "icon/rain-day.png",              night: "icon/rain-night.png" },

        // Abhi inka exact icon nahi hai, to closest fallback use ho raha hai
        65: { day: "icon/rain-day.png",              night: "icon/rain-night.png" },   // heavy rain
        71: { day: "icon/cloudy-day.png",            night: "icon/cloudy-night.png" }, // light snow
        73: { day: "icon/cloudy-day.png",            night: "icon/cloudy-night.png" }, // snow
        75: { day: "icon/cloudy-day.png",            night: "icon/cloudy-night.png" }, // heavy snow

        80: { day: "icon/rain-day.png",              night: "icon/rain-night.png" },   // rain showers
        81: { day: "icon/rain-day.png",              night: "icon/rain-night.png" },   // rain showers
        82: { day: "icon/rain-day.png",              night: "icon/rain-night.png" },   // heavy showers

        95: { day: "icon/rain-day.png",              night: "icon/rain-night.png" },   // thunderstorm
        96: { day: "icon/rain-day.png",              night: "icon/rain-night.png" },   // thunderstorm
        99: { day: "icon/rain-day.png",              night: "icon/rain-night.png" }    // severe thunderstorm
    };

    const selectedIcon = iconMap[weatherCode] || iconMap[2];
    return isDay ? selectedIcon.day : selectedIcon.night;
}

function updateWeatherIcon(weatherCode = currentWeatherCode) {
    currentWeatherCode = weatherCode;

    if (!weatherIcon) return;

    weatherIcon.src = getWeatherIconPath(weatherCode);
    weatherIcon.alt = "Weather condition icon";
}

// Har 1 min me check karega ki day/night change hua ya nahi
setInterval(() => {
    updateWeatherIcon(currentWeatherCode);
}, 60000);
// =======================================
// ============Risk-bar===================
// =======================================

function updateRiskBars(rain, wind, temperature){
    //Rain: already 0-100%
    const rainPercent=Math.min(rain,100);
    //Wind: 60km/h=full bar
    const windPercent=Math.min((wind/60)*100,100);
    //Temperature:20 C -> 0%, 45C-> 100%
    const heatPercent=Math.min(Math.max(((temperature-20)/25)*100,0),100);

    document.querySelector(".rain-bar").style.width=rainPercent+"%";
    document.querySelector(".wind-bar").style.width=windPercent+"%";
    document.querySelector(".heat-bar").style.width=heatPercent+"%";

    document.querySelector(".rain-level").textContent=
        rain<30 ? "Low":
        rain<70 ? "Moderate":"High";
    document.querySelector(".wind-level").textContent=
        wind<20 ? "Low":
        wind<40 ? "Moderate":"High";
    document.querySelector(".heat-level").textContent=
        temperature<30 ? "Low":
        temperature<38 ? "Moderate":"High";
}
//Abhi testing
updateRiskBars(1,80,21);
// ============================================================
// ======================Temp-active===========================
// ============================================================

async function updateCurrentWeathter(latitude, longitude){
    const response= await fetch(
        `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&current=temperature_2m,weather_code&timezone=auto`
    );

    if(!response.ok){
        throw new Error("Weather API Error");
    }
    const weatherData= await response.json();

    const temperature=Math.round(
        weatherData.current.temperature_2m
    );

    const weatherCode= weatherData.current.weather_code;

    const conditions={
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Cloudy",
        45: "Fog",
        48: "Fog",
        51: "Light drizzle",
        53: "Drizzle",
        55: "Heavy drizzle",
        61: "Light rain",
        63: "Rain",
        65: "Heavy rain",
        71: "Light snow",
        73: "Snow",
        75: "Heavy snow",
        80: "Rain showers",
        81: "Rain showers",
        82: "Heavy showers",
        95: "Thunderstorm",
        96: "Thunderstorm",
        99: "Severe thunderstorm"
    };

    document.querySelector(".main-temp-val h1").textContent=temperature;
    document.querySelector(".condition").textContent=conditions[weatherCode]||"Weather";

    updateWeatherIcon(weatherCode);
}

// ===========================
// const location=data.results[0];
// updateCurrentWeathter(location.latitude, location.longitude);
// ===================================================================
// ================Weather result live================================
// ===================================================================
async function updateFourWeatherBoxes(latitude, longitude) {

    const response = await fetch(
        `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&current=temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,weather_code&hourly=precipitation_probability&daily=uv_index_max&timezone=auto&forecast_days=1`
    );

    if (!response.ok) {
        throw new Error("Weather details API error");
    }

    const data = await response.json();

    // ===== HUMIDITY =====
    const humidity = data.current.relative_humidity_2m;

    const humidityLevel =
        humidity < 40 ? "Dry" :
        humidity <= 60 ? "Comfortable" :
        humidity <= 75 ? "Humid" :
        "Uncomfortable";

    document.querySelector(".Humidity").textContent = humidityLevel;
    document.querySelector(".Box1 .data").textContent =
        Math.round(humidity) + "%";


    // ===== WIND =====
    const wind = data.current.wind_speed_10m;
    const degree = data.current.wind_direction_10m;

    const directions = ["N","NE","E","SE","S","SW","W","NW"];

    const direction =
        directions[Math.round(degree / 45) % 8];

    const windLevel =
        wind < 10 ? "Calm" :
        wind < 20 ? "Breeze" :
        wind < 40 ? "Windy" :
        "Strong";

    document.querySelector(".Wind").textContent =
        `${direction} ${windLevel}`;

    document.querySelector(".Box2 .data").textContent =
        Math.round(wind) + " km/h";


    // ===== RAIN CHANCE =====
    const currentHour =
        data.current.time.slice(0, 13);

    let hourIndex = data.hourly.time.findIndex(
        time => time.startsWith(currentHour)
    );

    if (hourIndex === -1) {
        hourIndex = 0;
    }

    const rainChance =
        data.hourly.precipitation_probability[hourIndex] ?? 0;

    const rainLevel =
        rainChance < 30 ? "Low" :
        rainChance < 70 ? "Moderate" :
        "High";

    document.querySelector(".Rain-Chance").textContent =
        rainLevel;

    document.querySelector(".Box3 .data").textContent =
        Math.round(rainChance) + "%";


    // ===== UV INDEX =====
    const uv = data.daily.uv_index_max[0];

    const uvLevel =
        uv < 3 ? "Low" :
        uv < 6 ? "Moderate" :
        uv < 8 ? "High" :
        uv < 11 ? "Very High" :
        "Extreme";

    document.querySelector(".UV-Index").textContent =
        uvLevel;

    document.querySelector(".Box4 .data").textContent =
        Math.round(uv);

    const weatherCode=data.current.weather_code;
    // ===== RISK BARS =====
    updateRiskBars(
        rainChance,
        wind,
        data.current.temperature_2m
    );
    //Weathert risk
    updateWeatherAlert(rainChance,wind,data.current.temperature_2m,weatherCode);
}
// updateFourWeatherBoxes(location.latitude,location.longitude);
// ===========================================================
// ===================Own Predicted Alert bar=================
// ===========================================================
function updateWeatherAlert(rain,wind,temperature,weatherCode){
    const alertBox=document.querySelector(".alert-result");

    let message="No severe weather risk detected";
    let danger=false;

    if(weatherCode>=95){
        message="Thunderstorm risk detected";
        danger=true;
    }
    else if(wind>=40){
        message="Strong wind risk detected";
        danger=true;
    }
    else if(temperature>=40){
        message="High heat risk detected";
        danger=true;
    }
    else if(rain>=80){
        message="High rain possibility detected";
        danger=true;
    }
    if (danger){
        alertBox.classList.add("danger");
        alertBox.classList.remove("safe");
        alertBox.innerHTML=
            `<span class="status-icon">
                <i class="fa-solid fa-xmark"></i>
            </span>
            ${message}`;
    }else{
        alertBox.classList.add("safe");
        alertBox.classList.remove("danger");
        alertBox.innerHTML=
            `<span class="status-icon">
                <i class="fa-solid fa-check"></i>
            </span>
            ${message}`;
    }
}

// ==========================================================
// ================= WeatherGPT CHATBOT ======================
// ==========================================================

const chatArea = document.querySelector(".chat-area");
const chatInput = document.querySelector(".chat-input input");
const chatSendButton = document.querySelector(".chat-send button");

let chatBusy = false;

const CHAT_STORAGE_KEY = "weathergpt-chat-history";

// ----------------------------------------------------------
// Scroll chat automatically
// ----------------------------------------------------------

function scrollChat() {
    requestAnimationFrame(() => {
        chatArea.scrollTop = chatArea.scrollHeight;
    });
}


// ----------------------------------------------------------
// Save chat history
// ----------------------------------------------------------

function saveChatMessage(role, message) {

    let history = JSON.parse(
        localStorage.getItem(CHAT_STORAGE_KEY) || "[]"
    );

    history.push({
        role: role,
        message: message
    });

    // Only keep last 30 messages
    history = history.slice(-30);

    localStorage.setItem(
        CHAT_STORAGE_KEY,
        JSON.stringify(history)
    );
}


// ----------------------------------------------------------
// Add USER message
// ----------------------------------------------------------

function addUserMessage(message, save = true) {

    const userBox = document.createElement("div");

    userBox.className = "chat-box2";

    const messageBox = document.createElement("div");
    messageBox.className = "chat2 text-chat";

    const paragraph = document.createElement("p");
    paragraph.style.margin = "10px";
    paragraph.textContent = message;

    messageBox.appendChild(paragraph);
    userBox.appendChild(messageBox);

    chatArea.appendChild(userBox);

    if (save) {
        saveChatMessage("user", message);
    }

    scrollChat();
}


// ----------------------------------------------------------
// Add AI message
// ----------------------------------------------------------

function addAIMessage(message, save = false) {

    const aiBox = document.createElement("div");

    aiBox.className = "chat-box3";

    const symbol = document.createElement("div");
    symbol.className = "chat-symbol miniSymbol";

    const heading = document.createElement("h3");
    heading.textContent = "W";

    symbol.appendChild(heading);


    const textBox = document.createElement("div");
    textBox.className = "chat3 text-chat";


    const paragraph = document.createElement("p");
    paragraph.style.margin = "10px";
    paragraph.textContent = message;


    textBox.appendChild(paragraph);

    aiBox.appendChild(symbol);
    aiBox.appendChild(textBox);

    chatArea.appendChild(aiBox);


    if (save) {
        saveChatMessage("assistant", message);
    }


    scrollChat();

    // We return paragraph so Thinking... can be replaced later
    return paragraph;
}


// ----------------------------------------------------------
// Loading animation
// ----------------------------------------------------------

function showThinking() {

    const thinking = addAIMessage("");

    thinking.innerHTML = `
        <span class="thinking-text">
            Thinking
            <span class="thinking-dots">
                <span>.</span>
                <span>.</span>
                <span>.</span>
            </span>
    `;

    return thinking;
}


// ----------------------------------------------------------
// Disable / enable send button
// ----------------------------------------------------------

function setChatLoading(isLoading) {

    chatBusy = isLoading;

    chatSendButton.disabled = isLoading;

    if (isLoading) {

        chatSendButton.classList.add("sending");

    } else {

        chatSendButton.classList.remove("sending");

    }
}


// ----------------------------------------------------------
// Send message
// ----------------------------------------------------------

async function sendChatMessage() {

    const question = chatInput.value.trim();

    if (!question || chatBusy) {
        return;
    }


    // show user message
    addUserMessage(question);


    // clear input
    chatInput.value = "";


    // lock send button
    setChatLoading(true);


    // show Thinking...
    const loadingMessage = showThinking();


    try {

        const response = await fetch(
            "http://127.0.0.1:8000/chat",
            {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({

                    question: question,

                    latitude: currentLatitude,

                    longitude: currentLongitude

                })
            }
        );


        if (!response.ok) {

            throw new Error(
                "Backend error: " + response.status
            );
        }


        const data = await response.json();


        const answer =
            data.answer ||
            "Weather response nahi mila.";
        

        // Replace Thinking with real answer
        loadingMessage.textContent = answer;

        //Voice se question aaya tha to answer ko bolkar sunao
        if(voiceMessageActive){
            speakWeatherGPT(answer);
            voiceMessageActive=false;
        }

        // Save AI answer
        saveChatMessage(
            "assistant",
            answer
        );


        scrollChat();

    }

    catch (error) {

        console.error(
            "CHAT ERROR:",
            error
        );


        loadingMessage.textContent =
            "WeatherGPT backend se connect nahi ho pa raha. Please try again.";


    }

    finally {

        setChatLoading(false);

        chatInput.focus();

    }
}


// ----------------------------------------------------------
// SEND BUTTON
// ----------------------------------------------------------

chatSendButton.addEventListener(
    "click",
    sendChatMessage
);


// ----------------------------------------------------------
// ENTER KEY
// ----------------------------------------------------------

chatInput.addEventListener(
    "keydown",
    function(event) {

        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {

            event.preventDefault();

            sendChatMessage();

        }
    }
);


// ----------------------------------------------------------
// Restore old chat after refresh
// ----------------------------------------------------------

function loadChatHistory() {

    const history = JSON.parse(
        localStorage.getItem(CHAT_STORAGE_KEY) || "[]"
    );


    history.forEach(chat => {

        if (chat.role === "user") {

            addUserMessage(
                chat.message,
                false
            );

        }

        else if (chat.role === "assistant") {

            addAIMessage(
                chat.message,
                false
            );

        }

    });


    scrollChat();
}


loadChatHistory();
// ============================================================
// =====================CLEAR CHAT HISTORY=====================
// ============================================================
const clearChatButton=document.querySelector(".clear-chat-btn");
clearChatButton.addEventListener("click",()=>{
    const confirmClear=confirm("Do you want to clear WeatherGPT chat history?");

    if(!confirmClear) return;
    //remove saved history
    localStorage.removeItem(CHAT_STORAGE_KEY);
    //Remove user+AI message from screen
    chatArea
        .querySelectorAll(".chat-box2, .chat-box3")
        .forEach(message=> message.remove());
    //Scroll back to top
    chatArea.scrollTop=0;
    chatInput.focus();
});

// =======================================================================
// ============================VOICE INPUT================================
// =======================================================================

// ============================================================
// ================ WEATHERGPT VOICE CHAT V2 ==================
// ============================================================

const weatherVoiceButton =
    document.querySelector(".voice-btn button");

const weatherVoiceInput =
    document.querySelector(".chat-input input");

const voiceButtonContainer =
    document.querySelector(".voice-btn");


// ------------------------------------------------------------
// Browser Speech Recognition
// ------------------------------------------------------------

const SpeechRecognition =
    window.SpeechRecognition ||
    window.webkitSpeechRecognition;

let recognition = null;

let isListening = false;

// Existing sendChatMessage() isko use karega
let voiceMessageActive = false;


// ============================================================
// =============== STOP SPEAKING BUTTON ========================
// ============================================================

// Button JS se automatically create hoga.
// HTML me kuch add karne ki zarurat nahi.

const stopSpeakingButton =
    document.createElement("button");

stopSpeakingButton.type = "button";

stopSpeakingButton.className =
    "stop-speaking-btn";

stopSpeakingButton.title =
    "Stop WeatherGPT voice";

stopSpeakingButton.innerHTML =
    `<i class="fa-solid fa-volume-xmark"></i>`;

stopSpeakingButton.style.display = "none";

voiceButtonContainer.appendChild(
    stopSpeakingButton
);


// Stop AI speech
stopSpeakingButton.addEventListener(
    "click",
    () => {

        window.speechSynthesis.cancel();

        stopSpeakingButton.style.display =
            "none";

        document.body.classList.remove(
            "weather-gpt-speaking"
        );
    }
);


// ============================================================
// ================= SPEECH RECOGNITION ========================
// ============================================================

if (SpeechRecognition) {

    recognition =
        new SpeechRecognition();

    recognition.continuous = false;

    recognition.interimResults = true;

    // Hinglish / Indian English
    recognition.lang = "en-IN";


    // --------------------------------------------------------
    // Listening starts
    // --------------------------------------------------------

    recognition.onstart = () => {

        isListening = true;

        weatherVoiceButton.classList.add(
            "listening"
        );

        weatherVoiceInput.placeholder =
            "Listening...";

        weatherVoiceButton.title =
            "Stop listening";

        console.log(
            "🎙️ WeatherGPT is listening..."
        );
    };


    // --------------------------------------------------------
    // Speech -> text
    // --------------------------------------------------------

    recognition.onresult = (event) => {

        let transcript = "";


        for (
            let i = event.resultIndex;
            i < event.results.length;
            i++
        ) {

            transcript +=
                event.results[i][0].transcript;
        }


        // Live recognized text
        weatherVoiceInput.value =
            transcript;


        const lastResult =
            event.results[
                event.results.length - 1
            ];


        // Speech finished
        if (lastResult.isFinal) {

            voiceMessageActive = true;

            recognition.stop();

            console.log(
                "✅ Voice text:",
                transcript
            );


            // IMPORTANT:
            // AUTO SEND NAHI HOGA.
            //
            // User Enter ya Send button
            // press karega.
        }
    };


    // --------------------------------------------------------
    // Listening ends
    // --------------------------------------------------------

    recognition.onend = () => {

        isListening = false;

        weatherVoiceButton.classList.remove(
            "listening"
        );

        weatherVoiceInput.placeholder =
            "Ask WeatherGPT...";

        weatherVoiceButton.title =
            "Ask with voice";

        console.log(
            "🎙️ Listening stopped"
        );
    };


    // --------------------------------------------------------
    // Recognition errors
    // --------------------------------------------------------

    recognition.onerror = (event) => {

        console.error(
            "Voice recognition error:",
            event.error
        );


        isListening = false;

        weatherVoiceButton.classList.remove(
            "listening"
        );

        weatherVoiceInput.placeholder =
            "Ask WeatherGPT...";


        if (event.error === "not-allowed") {

            alert(
                "Microphone permission allow karo."
            );

        }

        else if (
            event.error === "audio-capture"
        ) {

            alert(
                "Microphone detect nahi ho raha."
            );

        }

        else if (
            event.error === "no-speech"
        ) {

            console.log(
                "No speech detected."
            );
        }
    };


    // --------------------------------------------------------
    // Mic click
    // --------------------------------------------------------

    weatherVoiceButton.addEventListener(
        "click",
        () => {

            // WeatherGPT bol raha hai to stop karo
            window.speechSynthesis.cancel();

            stopSpeakingButton.style.display =
                "none";


            // Already listening
            if (isListening) {

                recognition.stop();

                return;
            }


            // New voice query
            weatherVoiceInput.value = "";

            voiceMessageActive = false;


            try {

                recognition.start();

            }

            catch (error) {

                console.log(
                    "Recognition start error:",
                    error
                );
            }
        }
    );

}

else {

    weatherVoiceButton.addEventListener(
        "click",
        () => {

            alert(
                "Voice recognition supported nahi hai. Chrome ya Edge use karo."
            );
        }
    );
}



// ============================================================
// ================= VOICE SELECTION ===========================
// ============================================================

function chooseWeatherGPTVoice(text) {

    const voices =
        window.speechSynthesis.getVoices();


    if (!voices.length) {

        return null;
    }


    // Check Hindi Unicode
    const containsHindi =
        /[\u0900-\u097F]/.test(text);


    // --------------------------------------------------------
    // Pure Hindi answer
    // --------------------------------------------------------

    if (containsHindi) {

        return (

            voices.find(
                voice =>
                    voice.lang === "hi-IN" &&
                    /Google|Microsoft/i.test(
                        voice.name
                    )
            )

            ||

            voices.find(
                voice =>
                    voice.lang === "hi-IN"
            )

            ||

            voices.find(
                voice =>
                    voice.lang.startsWith("hi")
            )

            ||

            null
        );
    }


    // --------------------------------------------------------
    // Hinglish / English
    // --------------------------------------------------------

    return (

        voices.find(
            voice =>
                voice.lang === "en-IN" &&
                /Google|Microsoft/i.test(
                    voice.name
                )
        )

        ||

        voices.find(
            voice =>
                voice.lang === "en-IN"
        )

        ||

        voices.find(
            voice =>
                voice.lang.startsWith("en")
        )

        ||

        null
    );
}



// ============================================================
// ================= WEATHERGPT SPEAK ==========================
// ============================================================

function speakWeatherGPT(text) {

    if (!text) return;


    // Previous answer stop
    window.speechSynthesis.cancel();


    const speech =
        new SpeechSynthesisUtterance(text);


    // Hindi letters present -> Hindi voice
    if (/[\u0900-\u097F]/.test(text)) {

        speech.lang = "hi-IN";

    } else {

        // Hinglish generally en-IN me clearer lagega
        speech.lang = "en-IN";
    }


    // Natural speaking speed
    speech.rate = 0.95;

    speech.pitch = 1;

    speech.volume = 1;


    const selectedVoice =
        chooseWeatherGPTVoice(text);


    if (selectedVoice) {

        speech.voice =
            selectedVoice;
    }


    // --------------------------------------------------------
    // Speech starts
    // --------------------------------------------------------

    speech.onstart = () => {

        stopSpeakingButton.style.display =
            "inline-flex";

        document.body.classList.add(
            "weather-gpt-speaking"
        );

        console.log(
            "🔊 WeatherGPT speaking..."
        );
    };


    // --------------------------------------------------------
    // Speech ends
    // --------------------------------------------------------

    speech.onend = () => {

        stopSpeakingButton.style.display =
            "none";

        document.body.classList.remove(
            "weather-gpt-speaking"
        );

        console.log(
            "🔇 WeatherGPT finished."
        );
    };


    speech.onerror = () => {

        stopSpeakingButton.style.display =
            "none";

        document.body.classList.remove(
            "weather-gpt-speaking"
        );
    };


    window.speechSynthesis.speak(
        speech
    );
}



// Browser voices kabhi thoda late load hote hain
window.speechSynthesis.onvoiceschanged =
    () => {

        window.speechSynthesis.getVoices();

    };

