document.addEventListener('DOMContentLoaded', () => {
    let registeredVehicleId = null;

    const registerForm = document.getElementById('register-form');
    const successMsg = document.getElementById('success-msg');
    const paymentCard = document.getElementById('payment-card');
    const btnPay = document.getElementById('btn-pay');
    const paymentSuccess = document.getElementById('payment-success');
    const plateInput = document.getElementById('plate-input');
    const plateDisplay = document.getElementById('plate-display');

    plateInput.addEventListener('input', () => {
        plateDisplay.textContent = plateInput.value.trim() || '__ ___ __';
    });

    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const ownerName = document.getElementById('owner-name').value.trim();
        const phone = document.getElementById('phone').value.trim();
        const plate = plateInput.value.trim();

        document.getElementById('err-name').textContent = '';
        document.getElementById('err-plate').textContent = '';

        let valid = true;
        if (!ownerName) {
            document.getElementById('err-name').textContent = 'Le nom est obligatoire.';
            document.getElementById('owner-name').classList.add('error');
            valid = false;
        } else {
            document.getElementById('owner-name').classList.remove('error');
        }

        if (!plate) {
            document.getElementById('err-plate').textContent = 'Le matricule est obligatoire.';
            plateInput.classList.add('error');
            valid = false;
        } else {
            plateInput.classList.remove('error');
        }

        if (!valid) return;

        const btn = document.getElementById('btn-register');
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Enregistrement...';
        btn.disabled = true;

        try {
            const res = await fetch('/api/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ owner_name: ownerName, plaque_immatriculation: plate, phone })
            });
            const data = await res.json();

            if (data.success) {
                registeredVehicleId = data.id;
                registerForm.style.display = 'none';
                successMsg.style.display = 'block';
                btnPay.disabled = false;
                btnPay.innerHTML = '<i class="fa-solid fa-credit-card"></i> Confirmer le Paiement — 2 500 DA';
            } else {
                if (data.error && data.error.toLowerCase().includes('matricule')) {
                    document.getElementById('err-plate').textContent = data.error;
                    plateInput.classList.add('error');
                } else {
                    showToast(data.error || "Erreur d'enregistrement", 'error');
                }
                btn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Enregistrer le Véhicule';
                btn.disabled = false;
            }
        } catch {
            showToast('Erreur réseau', 'error');
            btn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Enregistrer le Véhicule';
            btn.disabled = false;
        }
    });

    const btnGotoPayment = document.getElementById('btn-goto-payment');
    if (btnGotoPayment) {
        btnGotoPayment.addEventListener('click', () => {
            paymentCard.scrollIntoView({ behavior: 'smooth' });
        });
    }

    document.querySelectorAll('.method-option').forEach(opt => {
        opt.addEventListener('click', () => {
            document.querySelectorAll('.method-option').forEach(o => o.classList.remove('active'));
            opt.classList.add('active');
        });
    });

    btnPay.addEventListener('click', async () => {
        if (btnPay.disabled) return;
        if (!registeredVehicleId) {
            showToast("Enregistrez d'abord votre véhicule", 'error');
            return;
        }

        btnPay.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Traitement en cours...';
        btnPay.disabled = true;

        await new Promise(r => setTimeout(r, 2000));

        try {
            const res = await fetch(`/api/vehicles/${registeredVehicleId}/pay`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ amount: 2500 })
            });
            const data = await res.json();

            if (data.success) {
                document.getElementById('payment-details').style.display = 'none';
                document.querySelector('.payment-methods').style.display = 'none';
                btnPay.style.display = 'none';
                paymentSuccess.style.display = 'block';
                const ownerName = document.getElementById('owner-name').value.trim();
                document.getElementById('payment-success-msg').textContent =
                    `Bienvenue ${ownerName} ! Votre accès au parking est maintenant activé.`;
            } else {
                showToast(data.error || 'Erreur de paiement', 'error');
                btnPay.innerHTML = '<i class="fa-solid fa-credit-card"></i> Confirmer le Paiement';
                btnPay.disabled = false;
            }
        } catch {
            showToast('Erreur réseau', 'error');
            btnPay.innerHTML = '<i class="fa-solid fa-credit-card"></i> Confirmer le Paiement';
            btnPay.disabled = false;
        }
    });

    function showToast(msg, type = 'info') {
        let toast = document.getElementById('reg-toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'reg-toast';
            toast.className = 'toast';
            document.body.appendChild(toast);
        }
        toast.textContent = msg;
        toast.className = `toast ${type} show`;
        clearTimeout(toast._timer);
        toast._timer = setTimeout(() => toast.className = `toast ${type}`, 3500);
    }
});
