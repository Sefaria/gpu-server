{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "nerServer.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "nerServer.selectorLabels" -}}
app.kubernetes.io/name: sefaria-ner-server
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "nerServer.labels" -}}
helm.sh/chart: {{ include "nerServer.chart" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{ include "nerServer.selectorLabels" . }}
{{- end }}

{{- define "nerServer.serviceAccount.name" -}}
{{ .Values.serviceAccount.name | default .Release.Name }}
{{- end }}

{{- define "nerServer.configfiles.name" -}}
{{ .Values.serviceAccount.name | default .Release.Name }}-files
{{- end }}

