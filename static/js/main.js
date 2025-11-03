document.addEventListener('DOMContentLoaded', function() {
    // Script para el año del footer
    const yearSpan = document.getElementById('year');
    if (yearSpan) {
        yearSpan.textContent = new Date().getFullYear();
    }

    // Script para mostrar/ocultar contraseña
    const togglePassword = document.querySelector('#togglePassword');
    const passwordInput = document.querySelector('#id_password');
    const passwordIcon = document.querySelector('#togglePasswordIcon');

    if (togglePassword && passwordInput && passwordIcon) {
        togglePassword.addEventListener('click', function () {
            const currentType = passwordInput.getAttribute('type');
            const newType = currentType === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', newType);
            
            if (newType === 'password') {
                passwordIcon.classList.remove('bi-eye');
                passwordIcon.classList.add('bi-eye-slash');
            } else {
                passwordIcon.classList.remove('bi-eye-slash');
                passwordIcon.classList.add('bi-eye');
            }
        });
    }

    // Script para la barra de fortaleza de la contraseña
    const passwordInputForStrength = document.querySelector('#id_password');
    const strengthBar = document.getElementById('passwordStrengthBar');
    const strengthText = document.getElementById('passwordStrengthText');

    if (passwordInputForStrength && strengthBar && strengthText) {
        passwordInputForStrength.addEventListener('input', function() {
            const password = this.value;
            let score = 0;

            if (password.length >= 8) score++;
            if (/[a-z]/.test(password)) score++;
            if (/[A-Z]/.test(password)) score++;
            if (/[0-9]/.test(password)) score++;
            if (/[^A-Za-z0-9]/.test(password)) score++; // Símbolos

            let width = (score / 5) * 100;
            strengthBar.style.width = width + '%';
            strengthBar.setAttribute('aria-valuenow', width);

            strengthBar.classList.remove('bg-danger', 'bg-warning', 'bg-info', 'bg-success');

            if (password.length === 0) {
                // Si el campo está vacío, restaurar el texto de ayuda original de Django
                strengthText.textContent = '{{ form.password.help_text|escapejs }}'; // Usamos una variable de la plantilla
                strengthText.className = 'form-text mt-1';
            } else if (score <= 2) {
                strengthBar.classList.add('bg-danger');
                strengthText.textContent = 'Fortaleza: Débil';
                strengthText.className = 'form-text text-danger';
            } else if (score <= 3) {
                strengthBar.classList.add('bg-warning');
                strengthText.textContent = 'Fortaleza: Media';
                strengthText.className = 'form-text text-warning';
            } else if (score <= 4) {
                strengthBar.classList.add('bg-info');
                strengthText.textContent = 'Fortaleza: Fuerte';
                strengthText.className = 'form-text text-info';
            } else {
                strengthBar.classList.add('bg-success');
                strengthText.textContent = 'Fortaleza: Muy Fuerte';
                strengthText.className = 'form-text text-success';
            }
        });
    }

    // Script para formatear el RUT mientras se escribe
    const rutInput = document.querySelector('#id_rut');

    if (rutInput) {
        rutInput.addEventListener('input', function(e) {
            let rut = e.target.value.replace(/[^\dkK]/g, ''); // Solo números y K
            
            if (rut.length > 1) {
                let body = rut.slice(0, -1);
                let dv = rut.slice(-1).toUpperCase();
                
                // Formatear cuerpo con puntos
                let formattedBody = new Intl.NumberFormat('es-CL').format(body);
                
                e.target.value = `${formattedBody}-${dv}`;
            } else {
                e.target.value = rut;
            }
        });
    }

    // Vista previa de la foto y nombre de archivo
    const fotoInput = document.getElementById('id_foto_perfil');
    const fotoPreview = document.getElementById('fotoPreview');
    const fileNameSpan = document.getElementById('fileName');

    if (fotoInput && fotoPreview && fileNameSpan) {
        fotoInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    fotoPreview.setAttribute('src', e.target.result);
                    fotoPreview.style.display = 'block';
                }
                reader.readAsDataURL(file);
                fileNameSpan.textContent = file.name;
            } else {
                fotoPreview.style.display = 'none';
                fileNameSpan.textContent = 'Ningún archivo seleccionado';
            }
        });
    }
});
