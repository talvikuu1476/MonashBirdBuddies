const PRESIGN_API      = 'https://ajens8j2c5.execute-api.us-east-1.amazonaws.com/test/presignedURL';
const YOUR_BUCKET_NAME = 'team163-bucket';
const dropZone         = document.getElementById('dropZone');
const fileInput        = document.getElementById('fileInput');
const progressContainer= document.getElementById('progressContainer');
const progressBar      = document.getElementById('progressBar');
const uploadResult     = document.getElementById('uploadResult');

// —— URL hash take Cognito ID Token —— 
function getIdToken() {
  const hash = window.location.hash.startsWith('#')
    ? window.location.hash.slice(1)
    : window.location.hash;
  const params = new URLSearchParams(hash);
  return params.get('id_token');
}

dropZone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', (e) => {
  if (e.target.files.length) handleFile(e.target.files[0]);
});
['dragenter','dragover','dragleave','drop'].forEach(evt => {
  dropZone.addEventListener(evt, (e) => {
    e.preventDefault();
    e.stopPropagation();
  });
});
dropZone.addEventListener('dragover', () => dropZone.classList.add('dragover'));
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', (e) => {
  dropZone.classList.remove('dragover');
  const files = e.dataTransfer.files;
  if (files.length) handleFile(files[0]);
});

async function handleFile(file) {
  const idToken = getIdToken();
  if (!idToken) {
    alert('⚠️ No id_token was obtained, please log in first!');
    return;
  }

  uploadResult.textContent           = '';
  progressBar.style.width            = '0%';
  progressContainer.style.visibility = 'visible';

  try {
    uploadResult.textContent = 'Getting upload link...';
    const query = `?filename=${encodeURIComponent(file.name)}`;
    const resp = await fetch(PRESIGN_API + query, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${idToken}`
      }
    });
    if (!resp.ok) throw new Error(`Can't get presigned URL，status：${resp.status}`);
    const { uploadUrl, objectKey, contentType } = await resp.json();

    // 3. upload to S3
    uploadResult.textContent = 'Starting to upload file...';
    const xhr = new XMLHttpRequest();
    xhr.open('PUT', uploadUrl, true);
    if (contentType) xhr.setRequestHeader('Content-Type', contentType);

    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable) {
        const percent = Math.round((e.loaded / e.total) * 100);
        progressBar.style.width = percent + '%';
      }
    });
    xhr.onreadystatechange = () => {
      if (xhr.readyState === XMLHttpRequest.DONE) {
        if (xhr.status === 200) {
          progressBar.style.width = '100%';
          uploadResult.innerHTML = `<p class="success">Upload Successfully！</p>`;
        } else {
          throw new Error(`Upload failed, status：${xhr.status}`);
        }
      }
    };
    xhr.send(file);

  } catch (err) {
    progressContainer.style.visibility = 'hidden';
    uploadResult.innerHTML = `<p class="error">Upload error：${err.message}</p>`;
    console.error(err);
  }
}

const API_ENDPOINT_FIND_BY_SPECIES = "https://ajens8j2c5.execute-api.us-east-1.amazonaws.com/test/query_by_species";
const searchBtn = document.getElementById("searchBtn");
const speciesInput = document.getElementById("speciesInput");
const linksList = document.getElementById("linksList");

// get token
function getIdToken() {
  const hash = window.location.hash.startsWith("#")
    ? window.location.hash.slice(1)
    : window.location.hash;
  const params = new URLSearchParams(hash);
  return params.get("id_token");
}

searchBtn.addEventListener("click", () => {
  const idToken = getIdToken();
  if (!idToken) {
    alert("No id_token was obtained, please log in first!");
    return;
  }

  const raw = speciesInput.value.trim();
  if (!raw) {
    alert("Please enter at least one species (comma separated).");
    return;
  }
  const arr = raw.split(",").map(s => s.trim()).filter(s => s);
  if (!arr.length) {
    alert("Please enter a valid species list, for example: crow or crow,pigeon");
    return;
  }

  const qs = arr.map(sp => `species=${encodeURIComponent(sp)}`).join("&");
  const url = `${API_ENDPOINT_FIND_BY_SPECIES}?${qs}`;

  fetch(url, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${idToken}`
    }
  })
    .then(resp => {
      if (!resp.ok) throw new Error("HTTP error：" + resp.status);
      return resp.json();
    })
    .then(data => {
      linksList.innerHTML = "";
      if (Array.isArray(data.links) && data.links.length) {
        data.links.forEach(link => {
          const li = document.createElement("li");

          if (link.includes("/thumbnail/")) {
            const img = document.createElement("img");
            img.src = link;
            img.alt = "";
            img.style.width = "150px";
            img.style.margin = "4px";
            li.appendChild(img);
            
            const urlLink = document.createElement("a");
            urlLink.href = link;
            urlLink.target = "_blank";
            urlLink.textContent = link;
            urlLink.style.display = "block";
            urlLink.style.fontSize = "0.8rem";
            urlLink.style.marginTop = "4px";
            li.appendChild(urlLink);
            
          } else {
            const a = document.createElement("a");
              a.href        = link;
              a.target      = "_blank";
              a.textContent = link;        
              a.style.display   = "block";
              a.style.fontSize  = "0.8rem";
              a.style.marginTop = "4px";
              li.appendChild(a);
          }

          linksList.appendChild(li);
        });
      } else {
        const li = document.createElement("li");
        li.textContent = "No files were matched.";
        linksList.appendChild(li);
      }
    })
    .catch(err => {
      console.error(err);
      linksList.innerHTML = "";
      const li = document.createElement("li");
      li.textContent = "Query error, please check the console log.";
      linksList.appendChild(li);
    });
});

const API_ENDPOINT_FIND_BY_THUMB = "https://ajens8j2c5.execute-api.us-east-1.amazonaws.com/test/query";
const thumbBtn    = document.getElementById("thumbBtn");
const thumbInput  = document.getElementById("thumbInput");
const thumbResult = document.getElementById("thumbResult");

function getIdToken() {
  const hash = window.location.hash.startsWith("#")
    ? window.location.hash.slice(1)
    : window.location.hash;
  const params = new URLSearchParams(hash);
  return params.get("id_token");
}

thumbBtn.addEventListener("click", async () => {
  while (thumbResult.firstChild) {
    thumbResult.removeChild(thumbResult.firstChild);
  }

  const idToken = getIdToken();
  if (!idToken) {
    const errP = document.createElement("p");
    errP.className = "error";
    errP.textContent = "⚠️ No id_token was obtained, please log in first!";
    thumbResult.appendChild(errP);
    return;
  }

  const thumbUrl = thumbInput.value.trim();
  if (!thumbUrl) {
    const errP = document.createElement("p");
    errP.className = "error";
    errP.textContent = "⚠️ Please enter a thumbnail S3 URL first.";
    thumbResult.appendChild(errP);
    return;
  }

  thumbBtn.disabled = true;
  thumbBtn.textContent = "Searching...";

  try {
    const resp = await fetch(API_ENDPOINT_FIND_BY_THUMB, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${idToken}`
      },
      body: JSON.stringify({ thumbnail_url: thumbUrl })
    });
    if (!resp.ok) throw new Error("Backend return status：" + resp.status);

    const data = await resp.json();
    if (!data.full_image_url) throw new Error("The backend did not return full_image_url");

    const successP = document.createElement("p");
    successP.className = "success";
    successP.textContent = "Query successful!";
    thumbResult.appendChild(successP);

    const fullUrl = data.full_image_url;
    const filename = fullUrl.split("/").pop();
    const dlLink = document.createElement("a");
    dlLink.href = fullUrl;
    dlLink.textContent = "Check & download originnal picture.";
    dlLink.download = filename;  
    dlLink.target = "_blank";
    dlLink.style.display = "block";
    dlLink.style.marginTop = "8px";
    thumbResult.appendChild(dlLink);

  } catch (err) {
    console.error(err);
    const errP = document.createElement("p");
    errP.className = "error";
    errP.textContent = `❌ Query failed：${err.message}`;
    thumbResult.appendChild(errP);
  } finally {
    thumbBtn.disabled = false;
    thumbBtn.textContent = "Query";
  }
});

const API_ENDPOINT_GET_LABELS  = "https://ajens8j2c5.execute-api.us-east-1.amazonaws.com/test/edittag";
const API_ENDPOINT_UPDATE_TAGS = "https://ajens8j2c5.execute-api.us-east-1.amazonaws.com/test/edittag";

const urlsInput         = document.getElementById("urlsInput");
const fetchLabelsBtn    = document.getElementById("fetchLabelsBtn");
const currentLabelsArea = document.getElementById("currentLabelsArea");
const tagsInput         = document.getElementById("tagsInput");
const submitUpdateBtn   = document.getElementById("submitUpdateBtn");
const updateResultArea  = document.getElementById("updateResultArea");

function getIdToken() {
  const hash = window.location.hash.startsWith('#')
    ? window.location.hash.slice(1)
    : window.location.hash;
  const params = new URLSearchParams(hash);
  return params.get('id_token');
}

fetchLabelsBtn.addEventListener("click", async () => {
  currentLabelsArea.innerHTML = "";
  updateResultArea.innerHTML  = "";

  const idToken = getIdToken();
  if (!idToken) {
    currentLabelsArea.innerHTML = `<div class="error">⚠️ No id_token was obtained, please log in first!</div>`;
    return;
  }

  const rawUrls = urlsInput.value.trim();
  if (!rawUrls) {
    currentLabelsArea.innerHTML = `<div class="error">⚠️ Please enter at least one URL first, one per line.</div>`;
    return;
  }
  const urlList = rawUrls.split("\n").map(l => l.trim()).filter(l => l);
  if (!urlList.length) {
    currentLabelsArea.innerHTML = `<div class="error">⚠️ Invalid URL list, please check your input.</div>`;
    return;
  }

  fetchLabelsBtn.disabled = true;
  fetchLabelsBtn.textContent = "Searching...";

  try {
    const qs = urlList.map(u => "url=" + encodeURIComponent(u)).join("&");
    const resp = await fetch(`${API_ENDPOINT_GET_LABELS}?${qs}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${idToken}`
      }
    });
    if (!resp.ok) throw new Error("Backend return status：" + resp.status);
    const data = await resp.json();

    currentLabelsArea.innerHTML = "";
    const results = data.results || {};
    urlList.forEach(u => {
      const labels = results[u] || {};
      const section = document.createElement("div");
      section.style.marginBottom = "16px";

      const title = document.createElement("h3");
      title.textContent = `URL: ${u}`;
      title.style.fontSize = "0.95rem";
      title.style.color = "#1e40af";
      section.appendChild(title);

      const pre = document.createElement("pre");
      pre.textContent = JSON.stringify(labels, null, 2);
      section.appendChild(pre);

      currentLabelsArea.appendChild(section);
    });

  } catch (err) {
    console.error(err);
    currentLabelsArea.innerHTML = `<div class="error">❌ Query failed：${err.message}</div>`;
  } finally {
    fetchLabelsBtn.disabled = false;
    fetchLabelsBtn.textContent = "Get label";
  }
});

submitUpdateBtn.addEventListener("click", async () => {
  updateResultArea.innerHTML = "";

  const idToken = getIdToken();
  if (!idToken) {
    updateResultArea.innerHTML = `<div class="error">⚠️ No id_token was obtained, please log in first!</div>`;
    return;
  }

  const rawUrls = urlsInput.value.trim();
  if (!rawUrls) {
    updateResultArea.innerHTML = `<div class="error">⚠️ Please first enter a list of URLs above and get the current tabs.</div>`;
    return;
  }
  const urlList = rawUrls.split("\n").map(l => l.trim()).filter(l => l);
  if (!urlList.length) {
    updateResultArea.innerHTML = `<div class="error">⚠️ Invalid URL list, please check your input.</div>`;
    return;
  }

  let tagsObj;
  try {
    tagsObj = JSON.parse(tagsInput.value.trim());
    if (typeof tagsObj !== "object" || Array.isArray(tagsObj)) {
      throw new Error("Must be a {\"tag\":number, ...} Object");
    }
    Object.entries(tagsObj).forEach(([k, v]) => {
      if (typeof v !== "number") throw new Error(`Label "${k}" value must be a number`);
    });
  } catch (err) {
    updateResultArea.innerHTML = `<div class="error">⚠️ Tags dictionary JSON error：${err.message}</div>`;
    return;
  }

  const opType   = document.querySelector('input[name="opType"]:checked').value;
  const operation = parseInt(opType, 10); 

  submitUpdateBtn.disabled = true;
  submitUpdateBtn.textContent = "Uploading...";

  const payload = { url: urlList, operation, tags: tagsObj };

  try {
    const resp = await fetch(API_ENDPOINT_UPDATE_TAGS, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${idToken}`
      },
      body: JSON.stringify(payload)
    });
    if (!resp.ok) throw new Error("Backend return status：" + resp.status);
    const text = await resp.text();
    updateResultArea.innerHTML = `<div class="result">✅ Update successful</div>`;
  } catch (err) {
    console.error(err);
    updateResultArea.innerHTML = `<div class="error">❌ Update failed：${err.message}</div>`;
  } finally {
    submitUpdateBtn.disabled = false;
    submitUpdateBtn.textContent = "Update Tags";
  }
});

const API_ENDPOINT_DELETE_FILES = 'https://ajens8j2c5.execute-api.us-east-1.amazonaws.com/test/query_delete_files';
const deleteUrlsInput   = document.getElementById('deleteUrlsInput');
const deleteFilesBtn    = document.getElementById('deleteFilesBtn');
const deleteResultArea  = document.getElementById('deleteResultArea');

function getIdToken() {
  const hash = window.location.hash.startsWith("#")
    ? window.location.hash.slice(1)
    : window.location.hash;
  const params = new URLSearchParams(hash);
  return params.get("id_token");
}

deleteFilesBtn.addEventListener('click', async () => {
  deleteResultArea.innerHTML = '';

  const idToken = getIdToken();
  if (!idToken) {
    deleteResultArea.innerHTML = `<p class="error">⚠️ No id_token was obtained, please log in first!</p>`;
    return;
  }

  const raw = deleteUrlsInput.value.trim();
  if (!raw) {
    deleteResultArea.innerHTML = `<p class="error">⚠️ Please enter at least one URL first</p>`;
    return;
  }
  const urlList = raw
    .split('\n')
    .map(u => u.trim())
    .filter(u => u.length);
  if (!urlList.length) {
    deleteResultArea.innerHTML = `<p class="error">⚠️ Invalid URL List</p>`;
    return;
  }

  deleteFilesBtn.disabled = true;
  deleteFilesBtn.textContent = 'Deleting...';

  try {
    const resp = await fetch(API_ENDPOINT_DELETE_FILES, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${idToken}`
      },
      body: JSON.stringify({ urls: urlList })
    });

    const data = await resp.json();
    if (resp.ok) {
      deleteResultArea.innerHTML =
        `<p class="success">✅ Deletion successful:${data.message}</p>`;
    } else {
      deleteResultArea.innerHTML =
        `<p class="error">❌ Deletion failed:${data.message || resp.status}</p>`;
    }
  } catch (err) {
    console.error(err);
    deleteResultArea.innerHTML =
      `<p class="error">🚨 error:${err.message}</p>`;
  } finally {
    deleteFilesBtn.disabled = false;
    deleteFilesBtn.textContent = 'Delete selected files';
  }
});

const API_QUERY_ENDPOINT = 'https://ajens8j2c5.execute-api.us-east-1.amazonaws.com/test/Find_image_video';
const tagContainer      = document.getElementById('tagContainer');
const addTagBtn         = document.getElementById('addTagBtn');
const queryFilesBtn     = document.getElementById('queryFilesBtn');
const queryResultArea   = document.getElementById('queryResultArea');

function getIdToken() {
  const hash = window.location.hash.startsWith('#') 
    ? window.location.hash.slice(1) 
    : window.location.hash;
  return new URLSearchParams(hash).get('id_token');
}

function createTagRow() {
  const row = document.createElement('div');
  row.className = 'form-row tag-row';

  const tagInput = document.createElement('input');
  tagInput.type = 'text';
  tagInput.className = 'form-control tag-input';
  tagInput.placeholder = 'Tag name (e.g. pigeon)';

  const countInput = document.createElement('input');
  countInput.type = 'number';
  countInput.className = 'form-control count-input';
  countInput.placeholder = 'Min count (e.g. 1)';
  countInput.min = '1';

  const removeBtn = document.createElement('button');
  removeBtn.type = 'button';
  removeBtn.className = 'btn btn-sm btn-danger remove-tag-btn';
  removeBtn.textContent = '×';
  removeBtn.addEventListener('click', () => {
    tagContainer.removeChild(row);
  });

  row.append(tagInput, countInput, removeBtn);
  tagContainer.appendChild(row);
}

function collectTags() {
  const tags = {};
  document.querySelectorAll('.tag-row').forEach(row => {
    const tag = row.querySelector('.tag-input').value.trim();
    const count = parseInt(row.querySelector('.count-input').value, 10);
    if (tag && !isNaN(count) && count > 0) {
      tags[tag] = count;
    }
  });
  return tags;
}

if (tagContainer.querySelectorAll('.tag-row').length === 0) {
  createTagRow();
}

addTagBtn.addEventListener('click', createTagRow);

queryFilesBtn.addEventListener('click', async () => {
  queryResultArea.innerHTML = '';
  const idToken = getIdToken();
  if (!idToken) {
    const p = document.createElement('p');
    p.className = 'error';
    p.textContent = '⚠️ No id_token was obtained, please log in first!';
    queryResultArea.appendChild(p);
    return;
  }

  const tags = collectTags();
  if (Object.keys(tags).length === 0) {
    const p = document.createElement('p');
    p.className = 'error';
    p.textContent = '⚠️ Please fill in at least one valid Tag and Count.';
    queryResultArea.appendChild(p);
    return;
  }

  queryFilesBtn.disabled = true;
  queryFilesBtn.textContent = 'Searching...';

  try {
    const resp = await fetch(API_QUERY_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${idToken}`
      },
      body: JSON.stringify({ tags })
    });

    const data = await resp.json();
    if (!resp.ok) throw new Error(data.message || resp.statusText);


    let ul = queryResultArea.querySelector('ul.links-list');
    if (!ul) {
      ul = document.createElement('ul');
      ul.className = 'links-list';
      queryResultArea.appendChild(ul);
    }

    ul.innerHTML = '';
    if (!Array.isArray(data.links) || data.links.length === 0) {
      const li = document.createElement('li');
      li.textContent = 'ℹ️ No files matching the criteria were found.';
      ul.appendChild(li);
    } else {
      data.links.forEach(link => {
        const li = document.createElement('li');

        const img = document.createElement('img');
        img.src = link;
        img.alt = '';
        img.style.width       = '150px';
        img.style.objectFit   = 'cover';
        img.style.display     = 'block';
        img.style.marginBottom= '4px';
        li.appendChild(img);

        const a = document.createElement('a');
        a.href        = link;
        a.textContent = link;
        a.target      = '_blank';
        a.style.display    = 'block';
        a.style.fontSize   = '0.8rem';
        a.style.color      = '#0066cc';
        li.appendChild(a);

        ul.appendChild(li);
      });
    }
    

  } catch (err) {
    console.error(err);
    const p = document.createElement('p');
    p.className = 'error';
    p.textContent = `🚨 Query failed:${err.message}`;
    queryResultArea.appendChild(p);
  } finally {
    queryFilesBtn.disabled = false;
    queryFilesBtn.textContent = 'Query File';
  }
});

const API_ENDPOINT_DETECT = 'https://ajens8j2c5.execute-api.us-east-1.amazonaws.com/test/query_files';

const detectInput      = document.getElementById('detectInput');
const detectBtn        = document.getElementById('detectBtn');
const detectResultArea = document.getElementById('detectResultArea');

function getIdToken() {
  const hash = window.location.hash.startsWith('#')
    ? window.location.hash.slice(1)
    : window.location.hash;
  return new URLSearchParams(hash).get('id_token');
}

detectBtn.addEventListener('click', async () => {
  detectResultArea.innerHTML = '';

  const idToken = getIdToken();
  if (!idToken) {
    const errP = document.createElement('p');
    errP.className = 'error';
    errP.textContent = '⚠️ No id_token was obtained, please log in first!';
    return detectResultArea.appendChild(errP);
  }

  const mediaUrl = detectInput.value.trim();
  if (!mediaUrl) {
    const errP = document.createElement('p');
    errP.className = 'error';
    errP.textContent = '⚠️ Please enter the S3 URL';
    return detectResultArea.appendChild(errP);
  }

  detectBtn.disabled   = true;
  detectBtn.textContent = 'Searching...';

  try {
    const resp = await fetch(API_ENDPOINT_DETECT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${idToken}`
      },
      body: JSON.stringify({ media_url: mediaUrl })
    });
    if (!resp.ok) throw new Error('HTTP ' + resp.status);

    const data = await resp.json();

    const tagsP = document.createElement('p');
    tagsP.className = 'result-title';
    tagsP.textContent = 'Detected tags: ' + data.detected_labels.join(', ');
    detectResultArea.appendChild(tagsP);

    const listTitleP = document.createElement('p');
    listTitleP.className = 'result-title';
    listTitleP.textContent = 'List of files with the same tag:';
    detectResultArea.appendChild(listTitleP);

    const ul = document.createElement('ul');
    ul.className = 'links-list';
    data.query_by_species_result.links.forEach(url => {
      const li = document.createElement('li');

      if (url.includes('/thumbnail/')) {
        const img = document.createElement('img');
        img.src            = url;
        img.alt            = 'Thumbnail';
        img.style.display     = 'block';
        img.style.width       = '150px';
        img.style.objectFit   = 'cover';
        img.style.marginBottom= '4px';
        li.appendChild(img);
      }

      const a = document.createElement('a');
      a.href        = url;
      a.target      = '_blank';
      a.textContent = url;
      a.style.display  = 'block';
      a.style.fontSize = '0.8rem';
      a.style.color    = '#0066cc';
      li.appendChild(a);

      ul.appendChild(li);
    });
    detectResultArea.appendChild(ul);

    if (data.thumbnail_url) {
      const img = document.createElement('img');
      img.src            = data.thumbnail_url;
      img.alt            = 'Thumbnail';
      img.style.display      = 'block';
      img.style.width        = '150px';
      img.style.objectFit    = 'cover';
      img.style.marginTop    = '12px';
      detectResultArea.appendChild(img);
    }
  } catch (err) {
    console.error(err);
    const errP = document.createElement('p');
    errP.className = 'error';
    errP.textContent = `🚨 Query failed: ${err.message}`;
    detectResultArea.appendChild(errP);

  } finally {
    detectBtn.disabled   = false;
    detectBtn.textContent = 'Query files with the same tag';
  }
});
