const burger=document.querySelector('.burger');const nav=document.querySelector('#main-nav');
function closeMenu(){burger?.setAttribute('aria-expanded','false');nav?.classList.remove('open');}
burger?.addEventListener('click',()=>{const open=burger.getAttribute('aria-expanded')!=='true';burger.setAttribute('aria-expanded',String(open));nav.classList.toggle('open',open);});
document.addEventListener('keydown',event=>{if(event.key==='Escape'){closeMenu();}});
