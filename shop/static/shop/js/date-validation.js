// Валидация даты рождения на стороне клиента
document.addEventListener('DOMContentLoaded', function () {
    const birthDateInput = document.getElementById('id_birth_date');

    if (birthDateInput) {
        birthDateInput.addEventListener('change', function () {
            validateBirthDate(this);
        });
    }
});

function validateBirthDate(input) {
    const birthDate = new Date(input.value);
    const today = new Date();

    // Сброс пользовательской ошибки
    input.setCustomValidity('');

    // Проверка на будущую дату
    if (birthDate > today) {
        input.setCustomValidity('Дата рождения не может быть в будущем');
        return;
    }

    // Расчет возраста
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();

    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
        age--;
    }

    // Проверка на совершеннолетие
    if (age < 18) {
        input.setCustomValidity('Вам должно быть не менее 18 лет');
    }

    // Проверка на слишком старый возраст
    if (age > 120) {
        input.setCustomValidity('Указан некорректный возраст');
    }
}
