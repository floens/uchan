{{/*
Expand the name of the chart.
*/}}
{{- define "uchan.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "uchan.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "uchan.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "uchan.labels" -}}
helm.sh/chart: {{ include "uchan.chart" . }}
{{ include "uchan.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "uchan.selectorLabels" -}}
app.kubernetes.io/name: {{ include "uchan.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}


{{- define "uchan.postgresql.fullname" -}}
{{- include "common.names.dependency.fullname" (dict "chartName" "postgresql" "chartValues" .Values.postgresql "context" $) -}}
{{- end -}}

{{- define "uchan.databaseHost" -}}
{{- if .Values.postgresql.enabled }}
    {{- printf "%s" (include "uchan.postgresql.fullname" .) -}}
{{- else -}}
    {{- printf "%s" .Values.externalDatabase.host -}}
{{- end -}}
{{- end -}}

{{- define "uchan.databasePort" -}}
{{- if .Values.postgresql.enabled }}
    {{- printf "5432" -}}
{{- else -}}
    {{- printf "%d" (.Values.externalDatabase.port | int ) -}}
{{- end -}}
{{- end -}}

{{- define "uchan.databaseName" -}}
{{- if .Values.postgresql.enabled }}
    {{- printf "%s" .Values.postgresql.auth.database -}}
{{- else -}}
    {{- printf "%s" .Values.externalDatabase.database -}}
{{- end -}}
{{- end -}}

{{- define "uchan.databaseUser" -}}
{{- if .Values.postgresql.enabled }}
    {{- printf "%s" .Values.postgresql.auth.username -}}
{{- else -}}
    {{- printf "%s" .Values.externalDatabase.user -}}
{{- end -}}
{{- end -}}

{{- define "uchan.databaseSecretName" -}}
{{- if .Values.postgresql.enabled }}
    {{- if .Values.postgresql.auth.existingSecret -}}
        {{- printf "%s" .Values.postgresql.auth.existingSecret -}}
    {{- else -}}
        {{- printf "%s" (include "uchan.postgresql.fullname" .) -}}
    {{- end -}}
{{- else if .Values.externalDatabase.existingSecret -}}
    {{- include "common.tplvalues.render" (dict "value" .Values.externalDatabase.existingSecret "context" $) -}}
{{- else -}}
    {{- printf "%s-externaldb" (include "common.names.fullname" .) -}}
{{- end -}}
{{- end -}}


{{- define "uchan.rabbitmq.fullname" -}}
{{- include "common.names.dependency.fullname" (dict "chartName" "rabbitmq" "chartValues" .Values.rabbitmq "context" $) -}}
{{- end -}}

{{- define "uchan.brokerHost" -}}
{{- if .Values.rabbitmq.enabled }}
    {{- printf "%s" (include "uchan.rabbitmq.fullname" .) -}}
{{- else -}}
    {{- printf "%s" .Values.externalBroker.host -}}
{{- end -}}
{{- end -}}

{{- define "uchan.brokerPort" -}}
{{- if .Values.rabbitmq.enabled }}
    {{- printf "5672" -}}
{{- else -}}
    {{- printf "%d" (.Values.externalBroker.port | int ) -}}
{{- end -}}
{{- end -}}

{{- define "uchan.brokerUser" -}}
{{- if .Values.rabbitmq.enabled }}
    {{- printf "%s" .Values.rabbitmq.auth.username -}}
{{- else -}}
    {{- printf "%s" .Values.externalBroker.user -}}
{{- end -}}
{{- end -}}

{{- define "uchan.brokerVhost" -}}
{{- if .Values.rabbitmq.enabled }}
    {{- printf "/" -}}
{{- else -}}
    {{- printf "%s" .Values.externalBroker.vhost -}}
{{- end -}}
{{- end -}}

{{- define "uchan.brokerSecretName" -}}
{{- if .Values.rabbitmq.enabled }}
    {{- if .Values.rabbitmq.auth.existingPasswordSecret -}}
        {{- printf "%s" .Values.rabbitmq.auth.existingPasswordSecret -}}
    {{- else -}}
        {{- printf "%s" (include "uchan.rabbitmq.fullname" .) -}}
    {{- end -}}
{{- else if .Values.externalBroker.existingSecret -}}
    {{- include "common.tplvalues.render" (dict "value" .Values.externalBroker.existingSecret "context" $) -}}
{{- else -}}
    {{- printf "%s-externaldb" (include "common.names.fullname" .) -}}
{{- end -}}
{{- end -}}


{{- define "uchan.memcached.fullname" -}}
{{- include "common.names.dependency.fullname" (dict "chartName" "memcached" "chartValues" .Values.memcached "context" $) -}}
{{- end -}}

{{- define "uchan.memcachedHost" -}}
{{- if .Values.memcached.enabled }}
    {{- printf "%s" (include "uchan.memcached.fullname" .) -}}
{{- else -}}
    {{- printf "%s" .Values.externalMemcached.host -}}
{{- end -}}
{{- end -}}

{{- define "uchan.memcachedPort" -}}
{{- if .Values.memcached.enabled }}
    {{- printf "11211" -}}
{{- else -}}
    {{- printf "%d" (.Values.externalMemcached.port | int ) -}}
{{- end -}}
{{- end -}}

{{- define "uchan.varnish.fullname" -}}
{{- printf "%s-%s" (include "uchan.fullname" .) "varnish-cluster" -}}
{{- end -}}

{{- define "uchan.varnishHost" -}}
{{- if .Values.varnish.enabled }}
    {{- printf "%s" (include "uchan.varnish.fullname" .) -}}
{{- else -}}
    {{- printf "%s" .Values.externalVarnish.host -}}
{{- end -}}
{{- end -}}

{{- define "uchan.appEnvironment" }}
  - name: FLASK_APP
    value: uchan
  - name: SITE_URL
    value: {{ .Values.uchan.siteUrl }}
  - name: ASSET_URL
    value: {{ .Values.uchan.assetUrl }}
  - name: PROXY_FIXER_NUM_PROXIES
{{ if .Values.varnish.enabled }}
    value: "1"
{{ else }}
    value: "0"
{{ end }}

  - name: DATABASE_HOST
    value: {{ include "uchan.databaseHost" . | quote }}
  - name: DATABASE_PORT
    value: {{ include "uchan.databasePort" . | quote }}
  - name: DATABASE_NAME
    value: {{ include "uchan.databaseName" . | quote }}
  - name: DATABASE_USER
    value: {{ include "uchan.databaseUser" . | quote }}
  - name: DATABASE_PASSWORD
    valueFrom:
      secretKeyRef:
        name: {{ include "uchan.databaseSecretName" . }}
        key: password

  - name: BROKER_HOST
    value: {{ include "uchan.brokerHost" . | quote }}
  - name: BROKER_PORT
    value: {{ include "uchan.brokerPort" . | quote }}
  - name: BROKER_USER
    value: {{ include "uchan.brokerUser" . | quote }}
  - name: BROKER_VHOST
    value: {{ include "uchan.brokerVhost" . | quote }}
  - name: BROKER_PASSWORD
    valueFrom:
      secretKeyRef:
        name: {{ include "uchan.brokerSecretName" . }}
        key: rabbitmq-password

  - name: MEMCACHED_HOST
    value: {{ include "uchan.memcachedHost" . | quote }}
  - name: MEMCACHED_PORT
    value: {{ include "uchan.memcachedPort" . | quote }}

{{ if .Values.varnish.enabled }}
  - name: VARNISH_ENABLE_PURGING
    value: "true"
  - name: VARNISH_HOST
    value: {{ include "uchan.varnishHost" . | quote }}
{{ end }}

{{- end }}
