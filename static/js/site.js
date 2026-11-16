const burger=document.querySelector('.burger');const nav=document.querySelector('#main-nav');
function closeMenu(){burger?.setAttribute('aria-expanded','false');nav?.classList.remove('open');}
burger?.addEventListener('click',()=>{const open=burger.getAttribute('aria-expanded')!=='true';burger.setAttribute('aria-expanded',String(open));nav.classList.toggle('open',open);});
document.addEventListener('keydown',event=>{if(event.key==='Escape'){closeMenu();}});

// Progressive enhancement: forms and filtering also work without JavaScript.
for(const form of document.querySelectorAll('form[data-validate]')){
 form.noValidate=true;
 form.addEventListener('submit',event=>{
  let first=null;
  for(const field of form.querySelectorAll('input:not([type=hidden]),select,textarea')){
   if(field.disabled||field.type==='checkbox')continue;
   const errorId=field.id+'_client_error';let error=document.getElementById(errorId);
   if(!error){error=document.createElement('p');error.id=errorId;error.className='error';field.insertAdjacentElement('afterend',error);}
   let text='';
   if(field.required&&!field.value.trim())text='Заполните это поле.';
   else if(field.type==='email'&&field.value&&!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(field.value))text='Укажите почту в формате name@example.ru.';
   else if(field.dataset.phone&&field.value&&(!/^\+?[0-9 ()-]+$/.test(field.value)||field.value.replace(/\D/g,'').length<10||field.value.replace(/\D/g,'').length>15))text='Укажите телефон: от 10 до 15 цифр.';
   else if(field.maxLength>0&&field.value.length>field.maxLength)text=`Не больше ${field.maxLength} символов.`;
   else if(!field.validity.valid)text=field.validationMessage;
   error.textContent=text;field.setAttribute('aria-invalid',String(Boolean(text)));
   const descriptions=new Set((field.getAttribute('aria-describedby')||'').split(' ').filter(Boolean));descriptions.add(errorId);field.setAttribute('aria-describedby',[...descriptions].join(' '));
   if(text&&!first)first=field;
  }
  if(first){event.preventDefault();first.focus();}
 });
}
const catalog=document.querySelector('#catalog-filter');
if(catalog){
 let timer,controller;
 async function search(query){
  controller?.abort();controller=new AbortController();const status=document.querySelector('#catalog-status');const results=document.querySelector('#catalog-results');status.textContent='Ищем маршруты…';results.setAttribute('aria-busy','true');
  try{const response=await fetch(catalog.dataset.search+'?'+query,{signal:controller.signal});if(!response.ok)throw Error('Не удалось загрузить маршруты. Попробуйте ещё раз.');const data=await response.json();results.innerHTML=data.html;status.textContent='Поиск завершён. Найдено: '+data.count;}
  catch(error){if(error.name!=='AbortError')status.textContent=error.message;}
  finally{results.setAttribute('aria-busy','false');}
 }
 catalog.addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(()=>search(new URLSearchParams(new FormData(catalog))),400);});
 catalog.addEventListener('submit',event=>{event.preventDefault();search(new URLSearchParams(new FormData(catalog)));});
 document.querySelector('#catalog-results').addEventListener('click',event=>{const link=event.target.closest('.pagination a');if(link){event.preventDefault();search(new URL(link.href).searchParams);}});
}
const bookingForm=document.querySelector('#booking-form');
if(bookingForm){
 let timer,controller;
 async function calculate(){
  controller?.abort();controller=new AbortController();const status=document.querySelector('#quote-status');const result=document.querySelector('#quote-result');status.textContent='Считаем стоимость…';result.setAttribute('aria-busy','true');
  try{
   const response=await fetch(bookingForm.dataset.quote,{method:'POST',body:new FormData(bookingForm),signal:controller.signal});const data=await response.json();if(!response.ok)throw Error(data.error||'Расчёт недоступен.');
   result.replaceChildren();
   for(const row of data.rows){const p=document.createElement('p');p.textContent=`${row.name}: ${row.tariff}, ${Number(row.price).toLocaleString('ru-RU')} ₽`;result.append(p);}
   for(const row of data.extras){const p=document.createElement('p');p.textContent=`${row.name}: ${row.price} ₽ × ${row.quantity}`;result.append(p);}
   const total=document.createElement('strong');total.textContent=`Итого: ${Number(data.total).toLocaleString('ru-RU')} ₽`;result.append(total);status.textContent=data.seats>data.available?'Для новой брони недостаточно мест. Итоговое наличие проверяется при сохранении.':`Туристов: ${data.seats}. Расчёт обновлён.`;
  }catch(error){if(error.name!=='AbortError'){status.textContent=error instanceof SyntaxError?'Сервис расчёта временно недоступен. Повторите попытку.':error.message;result.textContent='Предыдущий расчёт недействителен.';}}
  finally{result.setAttribute('aria-busy','false');}
 }
 document.querySelector('#calculate').addEventListener('click',calculate);
 bookingForm.addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(calculate,600);});
 document.querySelector('#add-tourist').addEventListener('click',()=>{
  const total=document.querySelector('#id_tourists-TOTAL_FORMS');const n=Number(total.value);if(n>=10){document.querySelector('#quote-status').textContent='В одном бронировании не больше 10 туристов.';return;}
  const template=document.querySelector('#empty-tourist');const wrapper=document.createElement('div');wrapper.innerHTML=template.innerHTML.replaceAll('__prefix__',String(n));document.querySelector('#tourists').append(...wrapper.childNodes);total.value=String(n+1);document.querySelector(`#id_tourists-${n}-full_name`).focus();
 });
}
document.querySelector('#print')?.addEventListener('click',()=>window.print());
