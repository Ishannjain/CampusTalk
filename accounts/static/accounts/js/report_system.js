document.addEventListener('DOMContentLoaded', () => {
    const modalOverlay = document.getElementById('reportModalOverlay');
    const modalForm = document.getElementById('reportForm');
    const closeBtn = document.querySelector('.close-report-modal');
    const cancelBtn = document.querySelector('.btn-report-cancel');
    const toastContainer = document.getElementById('report-toast-container');
    
    let currentTargetType = null;
    let currentTargetId = null;

    // Show Toast Notification
    window.showReportToast = function(message, type = 'info') {
        if (!toastContainer) return;
        
        const toast = document.createElement('div');
        toast.className = `report-toast ${type}`;
        
        const icon = document.createElement('span');
        icon.innerHTML = type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️';
        
        const msg = document.createElement('span');
        msg.textContent = message;
        
        const closeToastBtn = document.createElement('button');
        closeToastBtn.className = 'toast-close';
        closeToastBtn.innerHTML = '&times;';
        closeToastBtn.onclick = () => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        };
        
        toast.appendChild(icon);
        toast.appendChild(msg);
        toast.appendChild(closeToastBtn);
        
        toastContainer.appendChild(toast);
        
        setTimeout(() => {
            if (toast.parentElement) {
                toast.style.opacity = '0';
                setTimeout(() => toast.remove(), 300);
            }
        }, 4000);
    };

    // Open Modal
    document.querySelectorAll('.btn-flag-content').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            currentTargetType = btn.getAttribute('data-target-type');
            currentTargetId = btn.getAttribute('data-target-id');
            
            if (modalOverlay) {
                modalOverlay.classList.add('active');
            }
        });
    });

    // Close Modal functions
    const closeModal = () => {
        if (modalOverlay) {
            modalOverlay.classList.remove('active');
            modalForm.reset();
            currentTargetType = null;
            currentTargetId = null;
        }
    };

    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    if (cancelBtn) cancelBtn.addEventListener('click', closeModal);
    
    // Close on outside click
    if (modalOverlay) {
        modalOverlay.addEventListener('click', (e) => {
            if (e.target === modalOverlay) closeModal();
        });
    }

    // Submit Report
    if (modalForm) {
        modalForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const submitBtn = modalForm.querySelector('.btn-report-submit');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Submitting...';

            const payload = {
                target_type: currentTargetType,
                target_id: currentTargetId,
                reason: document.getElementById('reportReason').value,
                description: document.getElementById('reportDescription').value
            };

            try {
                const response = await fetch('/api/reports/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();

                if (response.ok) {
                    showReportToast('Report submitted successfully. Thank you!', 'success');
                    closeModal();
                } else {
                    showReportToast(data.error || 'Failed to submit report.', 'error');
                }
            } catch (error) {
                showReportToast('A network error occurred. Please try again.', 'error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Submit Report';
            }
        });
    }
    
    // Fetch and show new notifications on page load
    async function fetchNotifications() {
        try {
            const response = await fetch('/api/notifications/');
            if (response.ok) {
                const data = await response.json();
                if (data.notifications && data.notifications.length > 0) {
                    data.notifications.forEach(n => {
                        showReportToast(n.message, 'info');
                    });
                    
                    // Mark as read
                    await fetch('/api/notifications/mark_read/', { method: 'POST' });
                }
            }
        } catch(e) {
            console.error("Error fetching notifications", e);
        }
    }
    
    // Only fetch if logged in (could check for a specific body class or just try and fail silently)
    fetchNotifications();
});
