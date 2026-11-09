// Branding remains readable when the PNG is missing, slow or blocked.
document.querySelectorAll('.alm-brandmark').forEach(frame=>{
 const image=frame.querySelector('.alm-logo');if(!image)return;
 const loaded=()=>frame.classList.toggle('alm-image-loaded',image.complete&&image.naturalWidth>0);
 image.addEventListener('load',loaded);image.addEventListener('error',()=>frame.classList.remove('alm-image-loaded'));loaded();
});
