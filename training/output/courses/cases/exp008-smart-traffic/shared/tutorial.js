/* 机器人小车智慧交通综合案例 · 实验页公共脚本：scrollspy + 章节 reveal
   母版: industry/ind05-industrial-inspection/shared/tutorial.js */
(function(){
  const secs=[...document.querySelectorAll('section.blk')];
  const links=[...document.querySelectorAll('.side a[href^="#"]')];
  function spy(){
    if(!secs.length) return;
    let cur=secs[0].id;
    for(const s of secs){ if(s.getBoundingClientRect().top<140) cur=s.id; }
    links.forEach(a=>a.classList.toggle('now', a.getAttribute('href')==='#'+cur));
  }
  window.addEventListener('scroll',spy,{passive:true}); spy();
  const io=new IntersectionObserver(es=>es.forEach(e=>{
    if(e.isIntersecting){ e.target.classList.add('on'); io.unobserve(e.target); }
  }),{threshold:.10});
  document.querySelectorAll('.blk').forEach(el=>io.observe(el));
})();