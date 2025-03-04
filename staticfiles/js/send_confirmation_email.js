document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("form");
    const spinner = document.getElementById("spinner");
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const emailField = document.getElementById("email");
        const email = emailField.value;
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        spinner.classList.remove("d-none");
        try {
            const response = await fetch("https://vms-api-hg6f.onrender.com/vms/auth/users/reset_password/", {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    email: email
                })
            });
            const status_code = response.status;
            if (status_code === 204) {
                alert("We’ve sent you an email to reset your password. Please check your inbox. The reset link will expire in 5 minutes.");
            } else if(status_code === 400) {
                const failed_response = await response.json();
                alert("User with given email does not exist.");
            } else {
                alert("Something went wrong, please try again later.");
            }
        } catch (err) {
            alert("Something went wrong, failed to send confirmation email. Please try again later.");
            console.error(err);
        }finally {
            spinner.classList.add("d-none");
            emailField.value = "";
        }
    });
});