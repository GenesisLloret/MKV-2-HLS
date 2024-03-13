var filePaths = [];
var streamsList = [];
var dataTrackInfo = "";

function openNewWindow(url) {
    fetch(
        `/open-new-window?url=${encodeURIComponent(url)}`,
        { method: 'PUT' }
    ).then(
        response => response.json()
    ).then(
        newWindowContent => {
            var newWindow = window.open("", "_blank");
            newWindow.document.write(newWindowContent);
        }
    );
}

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
    var dataTracksLoads = await getInfoTracksValues(status)
    console.log(dataTracksLoads);
    let fileStatusDetails = document.createElement('div');
    fileStatusDetails.classList.add('fileStatusDetails');
    fileStatusDetails.innerHTML = `
        <h3>Pistas a procesar</h3>
        <div class="counterTracksLoads">
            <span class="tagInfoStatusTrackLoad tagInfoStatusTrackLoadVideo">Videos<span>${(dataTracksLoads["video"]).length}</span></span>
            <span class="tagInfoStatusTrackLoad tagInfoStatusTrackLoadAudio">Audio<span>${(dataTracksLoads["audio"]).length}</span></span>
            <span class="tagInfoStatusTrackLoad tagInfoStatusTrackLoadSubs">Subtítulos<span>${(dataTracksLoads["subtitles"]).length}</span></span>
        </div>`;
    const progressContainerd = lastFileContent.querySelector('.progress-container');
    lastFileContent.insertBefore(fileStatusDetails, progressContainerd.nextSibling);
    let tracksDisplayDomVid = document.createElement('div');
    let tracksDisplayDomAud = document.createElement('div');
    let tracksDisplayDomSub = document.createElement('div');
    tracksDisplayDomVid.classList.add('tracksData');
    tracksDisplayDomAud.classList.add('tracksData');
    tracksDisplayDomSub.classList.add('tracksData');
    var domTrackDataVideo = [];
    var domTrackDataAudio = [];
    var domTrackDataSubs = [];
    dataTracksLoads["video"].forEach(e => { domTrackDataVideo.push(`
        <ul>
            <li><b>ID:</b>${e.index}</li>
            <li><b>CODEC:</b>${e.codec_name}</li>
            <li><b>PROFILE CODEC:</b>${e.profile}</li>
            <li><b>WIDTH:</b>${e.width}</li>
            <li><b>HEIGHT:</b>${e.height}</li>
            <li><b>ASPECT RATIO:</b>${e.display_aspect_ratio}</li>
            <li><b>FRAMERATE:</b>${e.r_frame_rate}</li>
            <li><b>AVG FRAMERATE:</b>${e.avg_frame_rate}</li>
            <li><b>BPS:</b>${e.tags["BPS-eng"]}</li>
            <li><b>DURATION:</b>${e.tags["DURATION-eng"]}</li>
            <li><b>NºFRAMES:</b>${e.tags["NUMBER_OF_FRAMES-eng"]}</li>
            <li><b>SIZE(Bytes):</b>${e.tags["NUMBER_OF_BYTES-eng"]}</li>
        </ul>`
    )});
    dataTracksLoads["audio"].forEach(e => { domTrackDataAudio.push(`
        <ul>
            <li><b>ID:</b>${e.index}</li>
            <li><b>CODEC:</b>${e.codec_name}</li>
            <li><b>CANALS:</b>${e.channel_layout}</li>
            <li><b>BITRATE:</b>${e.bit_rate}</li>
            <li><b>LANGUAGE:</b>${e.tags["language"]}</li>
            <li><b>TITLE:</b>${e.tags["title"]}</li>
            <li><b>BPS:</b>${e.tags["BPS-eng"]}</li>
            <li><b>DURATION:</b>${e.tags["DURATION-eng"]}</li>
            <li><b>NºFRAMES:</b>${e.tags["NUMBER_OF_FRAMES-eng"]}</li>
            <li><b>SIZE(Bytes):</b>${e.tags["NUMBER_OF_BYTES-eng"]}</li>
        </ul>`
    )});
    
    dataTracksLoads["subtitles"].forEach(e => { domTrackDataSubs.push(`
        <ul>
            <li><b>ID:</b>${e.index}</li>
            <li><b>CODEC:</b>${e.codec_name}</li>
            <li><b>LANGUAGE:</b>${e.tags["language"]}</li>
            <li><b>TITLE:</b>${e.tags["title"]}</li>
            <li><b>BPS:</b>${e.tags["BPS-eng"]}</li>
            <li><b>DURATION:</b>${e.tags["DURATION-eng"]}</li>
            <li><b>NºFRAMES:</b>${e.tags["NUMBER_OF_FRAMES-eng"]}</li>
            <li><b>SIZE(Bytes):</b>${e.tags["NUMBER_OF_BYTES-eng"]}</li>
        </ul>`
    )});
    tracksDisplayDomVid.innerHTML = domTrackDataVideo.join('');
    tracksDisplayDomAud.innerHTML = domTrackDataAudio.join('');
    tracksDisplayDomSub.innerHTML = domTrackDataSubs.join('');
    document.getElementsByClassName('tagInfoStatusTrackLoad')[0].appendChild(tracksDisplayDomVid);
    document.getElementsByClassName('tagInfoStatusTrackLoad')[1].appendChild(tracksDisplayDomAud);
    document.getElementsByClassName('tagInfoStatusTrackLoad')[2].appendChild(tracksDisplayDomSub);

}
document.getElementById('drop_zone').addEventListener('drop', function (event) {
    event.preventDefault();
    event.stopPropagation();
    var fileDetails = document.getElementById('file-details');
    fileDetails.style.display = 'block';
    fileDetails.innerHTML = '';
    for (let i = 0; i < event.dataTransfer.files.length; i++) {
        let file = event.dataTransfer.files[i];
        if (file.name.endsWith('.mkv')) {
            fileHandler.handleFileDrop(file.name).then(
                function (status) {
                    displayFilePaths(status);
                }
            );
        }
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

new QWebChannel(
    qt.webChannelTransport,
    function (channel) {
        window.fileHandler = channel.objects.fileHandler;
    }
);

async function getInfoTracksValues(video) {
    try {
        const response = await fetch(
            '//127.0.0.1:15580/procesar-video',
            {
                method: 'POST',
                headers: {
                    'Authorization': 'Basic ' + btoa(username + ":" + password),
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ video_path: video })
            }
        );
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
