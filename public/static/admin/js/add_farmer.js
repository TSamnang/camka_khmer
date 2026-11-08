
  // Profile photo circle uploader
  const wrap        = document.getElementById('profileUploadWrap');
  const fileInput   = document.getElementById('profilePhotoInput');
  const preview     = document.getElementById('profilePreview');
  const placeholder = document.getElementById('profilePlaceholder');

  wrap.addEventListener('click', () => fileInput.click());

  fileInput.addEventListener('change', () => {
    const file = fileInput.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      preview.src = e.target.result;
      preview.classList.remove('d-none');
      placeholder.classList.add('d-none');
    };
    reader.readAsDataURL(file);
  });

  // Drag-and-drop support
  wrap.addEventListener('dragover', (e) => { e.preventDefault(); wrap.classList.add('profile-upload-hover'); });
  wrap.addEventListener('dragleave', ()  => wrap.classList.remove('profile-upload-hover'));
  wrap.addEventListener('drop', (e) => {
    e.preventDefault();
    wrap.classList.remove('profile-upload-hover');
    const file = e.dataTransfer.files[0];
    if (!file || !file.type.startsWith('image/')) return;
    // Assign to the input for form submission
    const dt = new DataTransfer();
    dt.items.add(file);
    fileInput.files = dt.files;
    const reader = new FileReader();
    reader.onload = (ev) => {
      preview.src = ev.target.result;
      preview.classList.remove('d-none');
      placeholder.classList.add('d-none');
    };
    reader.readAsDataURL(file);
  });
