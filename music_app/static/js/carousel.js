// carousel.js
document.addEventListener('DOMContentLoaded', () => {
  const track = document.querySelector('.carousel-single-track');
  const cards = Array.from(document.querySelectorAll('.artist-card'));
  let currentIndex = 1; // Стартовый индекс активной карточки
  
  // Инициализация карусели
  function initCarousel() {
      // Добавляем клоны для бесконечного эффекта
      const cloneFirst = cards[0].cloneNode(true);
      const cloneLast = cards[cards.length - 1].cloneNode(true);
      track.prepend(cloneLast);
      track.append(cloneFirst);
      
      // Обновляем список карточек
      const allCards = track.querySelectorAll('.artist-card');
      currentIndex = 1;
      updateCarousel(true);
  }

  function updateCarousel(initial = false) {
      const cardWidth = cards[0].offsetWidth + 40; // Ширина + margin
      const newPosition = -currentIndex * cardWidth;
      
      track.style.transform = `translateX(${newPosition}px)`;
      
      track.querySelectorAll('.artist-card').forEach((card, index) => {
          card.classList.remove('active', 'prev', 'next', 'hidden');
          
          if(index === currentIndex) {
              card.classList.add('active');
          } else if(index === currentIndex - 1) {
              card.classList.add('prev');
          } else if(index === currentIndex + 1) {
              card.classList.add('next');
          } else {
              card.classList.add('hidden');
          }
      });

      // Бесшовный переход для бесконечной карусели
      if(!initial) {
          if(currentIndex >= track.children.length - 2) {
              setTimeout(() => {
                  track.style.transition = 'none';
                  currentIndex = 1;
                  track.style.transform = `translateX(-${currentIndex * cardWidth}px)`;
                  setTimeout(() => track.style.transition = 'transform 0.6s cubic-bezier(0.4, 0, 0.2, 1)');
              }, 600);
          }
          
          if(currentIndex <= 0) {
              setTimeout(() => {
                  track.style.transition = 'none';
                  currentIndex = track.children.length - 2;
                  track.style.transform = `translateX(-${currentIndex * cardWidth}px)`;
                  setTimeout(() => track.style.transition = 'transform 0.6s cubic-bezier(0.4, 0, 0.2, 1)');
              }, 600);
          }
      }
  }

  // Автопрокрутка
  let autoScroll = setInterval(() => {
      currentIndex++;
      updateCarousel();
  }, 5000);

  // Остановка при наведении
  track.parentElement.addEventListener('mouseenter', () => clearInterval(autoScroll));
  track.parentElement.addEventListener('mouseleave', () => {
      autoScroll = setInterval(() => {
          currentIndex++;
          updateCarousel();
      }, 5000);
  });

  initCarousel();
});