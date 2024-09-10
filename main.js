function validateForm()
{
	var name = document.getElementById('name').value;
	var email = document.getElementById('email').value;
	var phone = document.getElementById('phone').value;
	var errorMessage = '';
	if(name == '')
	{
		errorMessage += 'Please Enter Name.\n';
	}
	if(email == '')
	{
		errorMessage += 'Please Enter Email.\n';
	}
	if(phone == '')
	{
		errorMessage += 'Please Enter Phone.\n';
	}
	if(errorMessage != '')
	{
		alert(errorMessage);return false;
	}
	alert('Form Submited Successfully..');
	window.location.href = 'successmessage.html';
}