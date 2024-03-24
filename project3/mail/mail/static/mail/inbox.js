document.addEventListener('DOMContentLoaded', function() {

  // Use buttons to toggle between views
  document.querySelector('#inbox').addEventListener('click', () => load_mailbox('inbox'));
  document.querySelector('#sent').addEventListener('click', () => load_mailbox('sent'));
  document.querySelector('#archived').addEventListener('click', () => load_mailbox('archive'));
  document.querySelector('#compose').addEventListener('click', () => (compose_email()));

  // By default, load the inbox
  load_mailbox('inbox');

  document.querySelector('form#compose-form').addEventListener('submit', e => {
    	e.preventDefault();

		formEl = e.target;

		fetch('/emails', {
			method: 'POST',
			body: JSON.stringify({
				recipients: formEl.querySelector('#compose-recipients').value,
				subject: formEl.querySelector('#compose-subject').value,
				body: formEl.querySelector('#compose-body').value,
			})
		})
		.then(response => {
			console.log(response);
			if (response.ok) {
				return response.json();
			}
			return Promise.reject(response);
		})
		.then(result => {
			success_msg(result.message);
			load_mailbox('sent');
		})
		.catch((response) => {
			response.json().then((result) => {
				error_msg(result.error);
			})
			
		});
		
    	return false;
  })
});

function compose_email(subject='', recipients='', body='') {
  // Show compose view and hide other views
  document.querySelector('#emails-view').style.display = 'none';
  document.querySelector('#compose-view').style.display = 'block';
  document.querySelector('#email-view').style.display = 'none';

  document.querySelector('#compose-recipients').value = recipients;
  document.querySelector('#compose-subject').value = subject;
  document.querySelector('#compose-body').value = body;
}

function load_mailbox(mailbox) {  
  // Show the mailbox and hide other views
  document.querySelector('#email-view').style.display = 'none';
  document.querySelector('#compose-view').style.display = 'none';

  // Show the mailbox name
  document.querySelector('#emails-view').innerHTML = `<h3>${mailbox.charAt(0).toUpperCase() + mailbox.slice(1)}</h3>`;
  
  	fetch(`/emails/${mailbox}`)
	.then(response => response.json())
	.then(emails => {
		clear_emails();
		emails.forEach(email => {
			add_email(email, mailbox);
		})
	});

	document.querySelector('#emails-view').style.display = 'block';
}

function load_email(email_id, mailbox) {
	document.querySelector('#emails-view').style.display = 'none';
	document.querySelector('#compose-view').style.display = 'none';

	fetch(`/emails/${email_id}`)
	.then(response => response.json())
	.then(email => {

		fetch(`/emails/${email_id}`, {
			method: 'PUT',
			body: JSON.stringify({
				read: true
			})
		})
		
		emailViewEl = document.querySelector('#email-view');
		emailViewEl.querySelector('#email-from').innerText = email.sender;
		emailViewEl.querySelector('#email-to').innerText = email.recipients;
		emailViewEl.querySelector('#email-subject').innerText = email.subject;
		emailViewEl.querySelector('#email-timestamp').innerText = email.timestamp;
		emailViewEl.querySelector('#email-body').innerText = email.body;

		// reply btn
		document.querySelector('#email-reply-btn').addEventListener('click', () => {
			let subject = email.subject
			if (!email.subject.startsWith("Re: ")) {
				subject = "Re: " + email.subject
			}
			const sections = email.body.split('\n--------------------------------\n');
			console.log(sections[sections.length - 1]);
			sections[sections.length - 1] = `${email.timestamp} ${email.sender} wrote:\n` + sections[sections.length - 1] + "\n--------------------------------\n"
			let body = sections.join('\n--------------------------------\n');
			
			compose_email(subject=subject, recipients=email.sender, body=body)
		})

		// archive/unarchive btn
		if (mailbox != "sent") {
			archiveBtnEl = emailViewEl.querySelector('#email-archive-btn')
			archiveBtnEl.innerText = !!email.archived ? "Unarchive" : "Archive"
			archiveBtnEl.addEventListener('click', () => {
				fetch(`/emails/${email_id}`, {
					method: 'PUT',
					body: JSON.stringify({
						archived: !email.archived
					})
				})
				load_mailbox(!!email.archived ? 'inbox' : 'archive')
			})
			archiveBtnEl.style.display = 'block'
		} else {
			emailViewEl.querySelector('#email-archive-btn').style.display = 'none'
		}
	});

	document.querySelector('#email-view').style.display = 'block';
}

function add_email(email, mailbox) {
	parentEl = document.querySelector('#emails-view')

	const cardEl = document.createElement('div');
	cardEl.classList.add('card');
	cardEl.classList.add('rounded-0');
	cardEl.classList.add('email-card');
	if (email.read) {
		cardEl.classList.add('read-email')
	}

	cardBodyEl = document.createElement('div');
	cardBodyEl.classList.add('card-body');
	cardBodyEl.classList.add('row');

	firstColEl = document.createElement('div');
	firstColEl.classList.add('col')
	secondColEl = document.createElement('div');
	secondColEl.classList.add('col-6')
	thirdColEl = document.createElement('div');
	thirdColEl.classList.add('col')
	thirdColEl.classList.add('text-right')
	thirdColEl.classList.add('text-muted')

	// 1st col
	senderEl = document.createElement('b');
	senderEl.innerText = email.sender;
	firstColEl.appendChild(senderEl)

	// 2nd col
	subjectEl = document.createElement('span');
	subjectEl.innerText	= email.subject;
	secondColEl.appendChild(subjectEl)

	// 3rd col
	timestampEl = document.createElement('span');
	timestampEl.innerHTML = email.timestamp;
	thirdColEl.appendChild(timestampEl)

	cardBodyEl.appendChild(firstColEl)
	cardBodyEl.appendChild(secondColEl)
	cardBodyEl.appendChild(thirdColEl)	
	cardEl.appendChild(cardBodyEl)

	cardEl.addEventListener('click', function() {
		load_email(email.id, mailbox)
	});

	parentEl.appendChild(cardEl);
}

function clear_emails() {
	parentEl = document.querySelector('#emails-view')
	parentEl.querySelectorAll(".email-card").forEach(el => {
		el.remove()
	})
}

function clear_msg() {
	document.querySelectorAll(".msg").forEach(msgEl => {
		msgEl.style.display = 'none';
	});
}

function success_msg(content) {
	clear_msg()

	msgEl = document.querySelector("#success-msg");
	msgEl.querySelector(".msg-content").innerText = content;
	msgEl.style.display = 'block';
}

function error_msg(content) {
	clear_msg();

	msgEl = document.querySelector("#error-msg");
	msgEl.querySelector(".msg-content").innerText = content;
	msgEl.style.display = 'block';
}