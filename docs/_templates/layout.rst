{% extends "!layout.html" %}

{% block footer %}
{{ super() }}
<div style="text-align: center; padding-top: 10px;">
    <img src="{{ pathto('_static/UKRI.png', 1) }}" alt="UKRI Logo" style="width: 200px;">
    <p>&copy; 2024 ISIS Rutherford Appleton Laboratory UKRI</p>
</div>
{% endblock %}
