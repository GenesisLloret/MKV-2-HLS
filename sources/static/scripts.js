
new QWebChannel(
    qt.webChannelTransport,
    function (channel) { window.fileHandler = channel.objects.fileHandler; }
);
var filePaths = [];
var streamsList = [];
var dataTrackInfo = "";
var dataTracks;
const toggle = document.querySelector('.theme-toggle');
document.getElementById('theme-toggle').addEventListener('change', function (event) { document.documentElement.setAttribute('data-theme', event.target.checked ? 'dark' : 'light'); });
toggle.addEventListener('click', () => {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const switchToTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', switchToTheme);
});
const currentTheme = localStorage.getItem('theme') ? localStorage.getItem('theme') : null;
if (currentTheme) {
    document.documentElement.setAttribute('data-theme', currentTheme);
    if (currentTheme === 'dark') { toggle.checked = true; }
}
toggle.addEventListener('click', () => {
    document.documentElement.setAttribute('data-theme', switchToTheme);
    localStorage.setItem('theme', switchToTheme);
});
function openNewWindow(url) {
    fetch(
        `/open-new-window?url=${encodeURIComponent(url)}`,
        { method: 'PUT' }
    ).then(response => response.json()).then(
        newWindowContent => {
            var newWindow = window.open("", "_blank");
            newWindow.document.write(newWindowContent);
        }
    );
}
document.getElementById('drop_zone').addEventListener('drop', function (event) {
    event.preventDefault();
    event.stopPropagation();
    var fileDetails = document.getElementById('file-details');
    fileDetails.style.display = 'block';
    fileDetails.innerHTML = '';
    for (let i = 0; i < event.dataTransfer.files.length; i++) {
        let file = event.dataTransfer.files[i];
        if (file.name.endsWith('.mkv')) { fileHandler.handleFileDrop(file.name).then(function (status) { displayFilePaths(status); }); }
    }
    console.log(JSON.stringify(filePaths));
});
document.getElementById('drop_zone').addEventListener(
    'dragover',
    function (event) {
        event.preventDefault();
        event.stopPropagation();
    }
);
async function getInfoTracksValues(video) {
    try {
        const response = await fetch('//127.0.0.1:15580/procesar-video', {
            method: 'POST',
            headers: {
                'Authorization': 'Basic ' + btoa(username + ":" + password),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ video_path: video })
        });
        const data = await response.json();
        console.log(data);
        var videoTracks = [];
        var audioTracks = [];
        var subtitlesTracks = [];
        for (const stream of data.streams) {
            if (stream.length === 0) {
                titleStatus.innerText = "Error al obtener datos de MKV...";
                return "NO PISTAS DETECTADAS";
            } else {
                titleStatus.innerText = "Pistas obtenidas...";
                switch (stream.codec_type) {
                    case "video": videoTracks.push(stream); break;
                    case "audio": audioTracks.push(stream); break;
                    case "subtitle": subtitlesTracks.push(stream); break;
                }
            }
        }
        return { video: videoTracks, audio: audioTracks, subtitles: subtitlesTracks };
    } catch (error) {
        console.error('Error:', error);
    }
}
function updateProgressBar(percentage) {
    const progressBar = document.querySelector('.progress-bar');
    progressBar.style.width = `${percentage}%`;
}
async function prepararDatosPistas(dataTracks) {
    return {
        video: dataTracks.video.map(e => ({
            index: e.index,
            codec_name: e.codec_name,
            profile: e.profile,
            width: e.width,
            height: e.height,
            aspect_ratio: e.display_aspect_ratio,
            framerate: e.r_frame_rate,
            avg_framerate: e.avg_frame_rate,
            bps: e.tags["BPS-eng"],
            duration: e.tags["DURATION-eng"],
            num_frames: e.tags["NUMBER_OF_FRAMES-eng"],
            size_bytes: e.tags["NUMBER_OF_BYTES-eng"]
        })),
        audio: dataTracks.audio.map(e => ({
            index: e.index,
            codec_name: e.codec_name,
            channel_layout: e.channel_layout,
            bit_rate: e.bit_rate,
            language: e.tags["language"],
            title: e.tags["title"],
            bps: e.tags["BPS-eng"],
            duration: e.tags["DURATION-eng"],
            num_frames: e.tags["NUMBER_OF_FRAMES-eng"],
            size_bytes: e.tags["NUMBER_OF_BYTES-eng"]
        })),
        subtitles: dataTracks.subtitles.map(e => ({
            index: e.index,
            codec_name: e.codec_name,
            language: e.tags["language"],
            title: e.tags["title"],
            bps: e.tags["BPS-eng"],
            duration: e.tags["DURATION-eng"],
            num_frames: e.tags["NUMBER_OF_FRAMES-eng"],
            size_bytes: e.tags["NUMBER_OF_BYTES-eng"]
        }))
    };
}
function generarHTMLPistasGenerico(pistas) {
    return pistas.map((pista, index) => {
        const items = Object.entries(pista).map(([clave, valor]) => {
            if (typeof valor === 'object' && valor !== null && !Array.isArray(valor)) {
                const subItems = Object.entries(valor).map(([subClave, subValor]) =>
                    `<li><b>${subClave.toUpperCase().replace(/_/g, ' ')}:</b> ${subValor}</li>`
                ).join('');
                return `<li><b>${clave.toUpperCase().replace(/_/g, ' ')}:</b> <ul>${subItems}</ul></li>`;
            }
            return `<li><b>${clave.toUpperCase().replace(/_/g, ' ')}:</b> ${valor}</li>`;
        }).join('');
        return `<div id="trackInfo_${pista.index}" class="statusTrack">
                    <strong>Pista ${index + 1}</strong>
                    <span class="status">STATUS: datos técnicos obtenidos</span>
                    <details>
                        <summary>Datos</summary>
                        <ul class="specs">${items}<ul>
                    </details>                    
                </div>`;
    }).join('');
}
document.addEventListener("DOMContentLoaded", () => {
    const accordions = document.getElementsByClassName("accordion");
    for (let i = 0; i < accordions.length; i++) {
        accordions[i].addEventListener("click", function () {
            this.classList.toggle("active");
            var panel = this.nextElementSibling;
            if (panel.style.display === "block") { panel.style.display = "none"; }
            else {
                panel.style.display = "block";
            }
        });
    }
});
async function displayFilePaths(status) {
    const DragDrop = document.getElementById('drag-and-drop-area');
    DragDrop.classList.add('fadeOut');
    const fileDetails = document.getElementById('file-details');
    fileDetails.classList.add('fadeIn');
    let newFileDiv = document.createElement('article');
    newFileDiv.classList.add('fileContents');
    fileDetails.appendChild(newFileDiv);
    const fileContentsElements = fileDetails.querySelectorAll('.fileContents');
    const lastFileContent = fileContentsElements[fileContentsElements.length - 1];
    let titleStatus = document.createElement('strong');
    titleStatus.innerText = "Enviando video a procesar...";
    let progressContainer = document.createElement('div');
    let progressBar = document.createElement('div');
    progressContainer.classList.add('progress-container');
    progressBar.classList.add('progress-bar');
    progressContainer.appendChild(progressBar);
    lastFileContent.appendChild(titleStatus).setAttribute('id', 'titleStatus');
    lastFileContent.appendChild(progressContainer);
    dataTracks = await getInfoTracksValues(status);
    var datosPistasPreparados = await prepararDatosPistas(dataTracks);
    console.log(datosPistasPreparados);
    let fileStatusDetails = document.createElement('div');
    fileStatusDetails.classList.add('fileStatusDetails');
    fileStatusDetails.innerHTML = `
        <h3>Pistas a procesar</h3>
        <div class="counterTracksLoads">
            <span class="tagInfoStatusTrackLoad tagInfoStatusTrackLoadVideo">Videos<span>${(dataTracks["video"]).length}</span></span>
            <span class="tagInfoStatusTrackLoad tagInfoStatusTrackLoadAudio">Audio<span>${(dataTracks["audio"]).length}</span></span>
            <span class="tagInfoStatusTrackLoad tagInfoStatusTrackLoadSubs">Subtítulos<span>${(dataTracks["subtitles"]).length}</span></span>
        </div>`;
    let progressContainerd = lastFileContent.querySelector('.progress-container');
    lastFileContent.insertBefore(fileStatusDetails, progressContainerd.nextSibling);
    let tracksDisplayDomVid = document.createElement('div');
    let tracksDisplayDomAud = document.createElement('div');
    let tracksDisplayDomSub = document.createElement('div');
    tracksDisplayDomVid.classList.add('tracksData');
    tracksDisplayDomAud.classList.add('tracksData');
    tracksDisplayDomSub.classList.add('tracksData');
    let domTrackDataVideo = generarHTMLPistasGenerico(dataTracks.video);
    let domTrackDataAudio = generarHTMLPistasGenerico(dataTracks.audio);
    let domTrackDataSubs = generarHTMLPistasGenerico(dataTracks.subtitles);
    let domTrackData = [domTrackDataVideo, domTrackDataAudio, domTrackDataSubs];
    for (let i = 0; i < domTrackData.length; i++) {
        document.getElementsByClassName('tagInfoStatusTrackLoad')[i].insertAdjacentHTML('beforeend', domTrackData[i]);
    }
    updateProgressBar(25);
    titleStatus.classList.add('fadeOut');
    progressContainerd.classList.add('fadeOut');
    if (!document.getElementById('checkCompatibilityBtn')) {
        let checkCompatibilityBtn = document.createElement('button');
        checkCompatibilityBtn.id = 'checkCompatibilityBtn';
        checkCompatibilityBtn.classList.add('fadeIn');
        checkCompatibilityBtn.textContent = 'Comprobar Compatibilidad';
        checkCompatibilityBtn.addEventListener('click', checkCompatibility);
        fileDetails.appendChild(checkCompatibilityBtn);
    }
}
async function checkCompatibility() {
    const fileDetails = document.getElementById('file-details');
    document.getElementById('checkCompatibilityBtn').disabled = true;
    let titleStatus2 = fileDetails.querySelector('#titleStatus');
    let progressContainerd2 = fileDetails.querySelector('.progress-container');
    titleStatus2.classList.remove('fadeOut');
    progressContainerd2.classList.remove('fadeOut');
    titleStatus2.innerText = "Detectando compatibilidad...";
    let secondProgressContainer = document.createElement('div');
    secondProgressContainer.classList.add('progress-container');
    let secondProgressBar = document.createElement('div');
    secondProgressBar.classList.add('progress-bar');
    secondProgressContainer.appendChild(secondProgressBar);
    fileDetails.appendChild(secondProgressContainer);
    titleStatus2.classList.add('fadeIn');
    progressContainerd2.classList.add('fadeIn');
    let videoCompatibility = new Array(dataTracks.video.length).fill(null);
    let audioCompatibility = new Array(dataTracks.audio.length).fill(null);
    let subtitlesCompatibility = new Array(dataTracks.subtitles.length).fill(null);
    // Paso 4, 4a, 5: Lógica de extracción y comprobación
    // Esta es una representación simplificada; necesitarás implementar la lógica específica de comprobación.
    // Por ejemplo:
    videoCompatibility = videoCompatibility.map((_, index) => true); // Supongamos que todas son compatibles
    audioCompatibility = audioCompatibility.map((_, index) => true); // Igual para audio
    subtitlesCompatibility = subtitlesCompatibility.map((_, index) => Math.random() > 0.5); // Aleatorio para demostración
    // Paso 6: Mostrar por consola el valor de cada array
    console.log('Compatibilidad de Video:', videoCompatibility);
    console.log('Compatibilidad de Audio:', audioCompatibility);
    console.log('Compatibilidad de Subtítulos:', subtitlesCompatibility);
    var videos = document.getElementsByClassName('tagInfoStatusTrackLoadVideo');
    for (var i = 0; i < videoCompatibility.length; i++) {
        var statusElements = videos[0].getElementsByClassName('status');
        if (statusElements.length > 0) {
            statusElements[i].innerText = videoCompatibility[i] ? 'STATUS: Compatible' : 'STATUS: Incompatible';
        }
    }
    var audios = document.getElementsByClassName('tagInfoStatusTrackLoadAudio');
    for (var i = 0; i < audioCompatibility.length; i++) {
        var statusElements = audios[0].getElementsByClassName('status');
        if (statusElements.length > 0) {
            statusElements[i].innerText = audioCompatibility[i] ? 'STATUS: Compatible' : 'STATUS: Incompatible';
        }
    }
    var subs = document.getElementsByClassName('tagInfoStatusTrackLoadSubs');
    for (var i = 0; i < subtitlesCompatibility.length; i++) {
        var statusElements = subs[0].getElementsByClassName('status');
        if (statusElements.length > 0) {
            statusElements[i].innerText = subtitlesCompatibility[i] ? 'STATUS: Compatible' : 'STATUS: Incompatible';
        }
    }
    // Re-habilitar el botón después de la comprobación
    document.getElementById('checkCompatibilityBtn').disabled = false;
}
