// Only controls password visibility. Native forms, CSRF and authentication stay unchanged.
document.querySelectorAll('input[type="password"]').forEach(input=>{
 const field=document.createElement('div');field.className='password-field';input.before(field);field.append(input);
 const button=document.createElement('button');button.type='button';button.className='password-toggle';button.textContent='Mostrar';button.setAttribute('aria-label','Mostrar '+(input.id==='confirmation'?'confirmação de senha':'senha'));button.setAttribute('aria-controls',input.id);button.setAttribute('aria-pressed','false');
 button.onclick=()=>{const visible=input.type==='password';input.type=visible?'text':'password';button.textContent=visible?'Ocultar':'Mostrar';button.setAttribute('aria-pressed',String(visible));button.setAttribute('aria-label',(visible?'Ocultar ':'Mostrar ')+(input.id==='confirmation'?'confirmação de senha':'senha'))};field.append(button);
});
