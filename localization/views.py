from decimal import Decimal
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Country, CurrencyRate
from .serializers import CountrySerializer, CurrencyRateSerializer

class CountryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset=Country.objects.filter(active=True).order_by("name")
    serializer_class=CountrySerializer

class CurrencyRateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset=CurrencyRate.objects.all().order_by("-updated_at")
    serializer_class=CurrencyRateSerializer

    @action(detail=False, methods=["get"], url_path="convert")
    def convert(self, request):
        base=(request.query_params.get("base") or "").upper()
        quote=(request.query_params.get("quote") or "").upper()
        amount=Decimal(request.query_params.get("amount","0"))
        if base == quote:
            return Response({"base":base,"quote":quote,"amount":str(amount),"converted":str(amount),"rate":"1"})
        rate=CurrencyRate.objects.filter(base=base,quote=quote).first()
        if not rate:
            return Response({"detail":"No configured exchange rate for this pair."},status=404)
        converted=amount*rate.rate
        return Response({"base":base,"quote":quote,"amount":str(amount),"converted":str(converted),"rate":str(rate.rate)})
