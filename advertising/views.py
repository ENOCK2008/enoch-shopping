from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q, Sum, Count
from .models import (
    AdCampaign, VideoAd, Banner, ProductPromotion,
    AdMetrics, Sponsorship, AdRequest
)
from .serializers import (
    AdCampaignSerializer, VideoAdSerializer, BannerSerializer,
    ProductPromotionSerializer, AdMetricsSerializer, SponsorshipSerializer,
    AdRequestSerializer
)


class AdCampaignViewSet(viewsets.ModelViewSet):
    """ViewSet for managing ad campaigns"""
    serializer_class = AdCampaignSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return AdCampaign.objects.filter(advertiser=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(advertiser=self.request.user)
    
    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pause a campaign"""
        campaign = self.get_object()
        campaign.status = 'paused'
        campaign.save()
        return Response({'status': 'campaign paused'})
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a campaign"""
        campaign = self.get_object()
        campaign.status = 'active'
        campaign.save()
        return Response({'status': 'campaign activated'})
    
    @action(detail=True, methods=['get'])
    def metrics(self, request, pk=None):
        """Get campaign metrics"""
        campaign = self.get_object()
        metrics = {
            'impressions': campaign.impressions,
            'clicks': campaign.clicks,
            'conversions': campaign.conversions,
            'ctr': campaign.ctr,
            'conversion_rate': campaign.conversion_rate,
            'roi': campaign.roi,
            'budget': str(campaign.budget),
            'spent': str(campaign.spent),
            'remaining': str(campaign.budget - campaign.spent),
        }
        return Response(metrics)


class VideoAdViewSet(viewsets.ModelViewSet):
    """ViewSet for video advertisements"""
    serializer_class = VideoAdSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        campaign_id = self.request.query_params.get('campaign', None)
        if campaign_id:
            return VideoAd.objects.filter(campaign__advertiser=self.request.user, campaign_id=campaign_id)
        return VideoAd.objects.filter(campaign__advertiser=self.request.user)
    
    @action(detail=False, methods=['get'])
    def by_placement(self, request):
        """Get ads by placement"""
        placement = request.query_params.get('placement')
        if not placement:
            return Response({'error': 'placement parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        
        ads = VideoAd.objects.filter(placement=placement, active=True).order_by('-priority')[:3]
        serializer = self.get_serializer(ads, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def track_view(self, request, pk=None):
        """Track video view"""
        ad = self.get_object()
        ad.views += 1
        ad.save()
        
        # Record metric
        AdMetrics.objects.create(
            campaign=ad.campaign,
            video_ad=ad,
            metric_type='view',
            user=request.user if request.user.is_authenticated else None,
            session_id=request.session.session_key or '',
            ip_address=self._get_client_ip(request),
            device_type=self._get_device_type(request)
        )
        
        return Response({'status': 'view tracked'})
    
    @action(detail=True, methods=['post'])
    def track_click(self, request, pk=None):
        """Track ad click"""
        ad = self.get_object()
        ad.clicks += 1
        ad.save()
        ad.campaign.clicks += 1
        ad.campaign.save()
        
        AdMetrics.objects.create(
            campaign=ad.campaign,
            video_ad=ad,
            metric_type='click',
            user=request.user if request.user.is_authenticated else None,
            session_id=request.session.session_key or '',
            ip_address=self._get_client_ip(request),
            device_type=self._get_device_type(request)
        )
        
        return Response({'status': 'click tracked'})
    
    @staticmethod
    def _get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @staticmethod
    def _get_device_type(request):
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        if 'mobile' in user_agent or 'android' in user_agent:
            return 'mobile'
        elif 'tablet' in user_agent or 'ipad' in user_agent:
            return 'tablet'
        return 'desktop'


class BannerViewSet(viewsets.ModelViewSet):
    """ViewSet for banner advertisements"""
    serializer_class = BannerSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        campaign_id = self.request.query_params.get('campaign', None)
        if campaign_id:
            return Banner.objects.filter(campaign__advertiser=self.request.user, campaign_id=campaign_id)
        return Banner.objects.filter(campaign__advertiser=self.request.user)
    
    @action(detail=False, methods=['get'])
    def by_placement(self, request):
        """Get banners by placement"""
        placement = request.query_params.get('placement')
        if not placement:
            return Response({'error': 'placement parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        
        banners = Banner.objects.filter(placement=placement, active=True).order_by('-priority')[:2]
        serializer = self.get_serializer(banners, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def track_impression(self, request, pk=None):
        """Track banner impression"""
        banner = self.get_object()
        banner.impressions += 1
        banner.save()
        banner.campaign.impressions += 1
        banner.campaign.save()
        
        AdMetrics.objects.create(
            campaign=banner.campaign,
            banner=banner,
            metric_type='impression',
            user=request.user if request.user.is_authenticated else None,
            session_id=request.session.session_key or '',
        )
        
        return Response({'status': 'impression tracked'})


class ProductPromotionViewSet(viewsets.ModelViewSet):
    """ViewSet for product promotions"""
    serializer_class = ProductPromotionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ProductPromotion.objects.filter(campaign__advertiser=self.request.user)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active promotions"""
        promotions = ProductPromotion.objects.filter(active=True).select_related('product')
        serializer = self.get_serializer(promotions, many=True)
        return Response(serializer.data)


class SponsorshipViewSet(viewsets.ModelViewSet):
    """ViewSet for sponsorships"""
    serializer_class = SponsorshipSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Sponsorship.objects.filter(sponsor=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(sponsor=self.request.user)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active sponsorships"""
        now = timezone.now()
        sponsorships = Sponsorship.objects.filter(
            active=True,
            start_date__lte=now,
            end_date__gte=now
        )
        serializer = self.get_serializer(sponsorships, many=True)
        return Response(serializer.data)


class AdRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for ad requests"""
    serializer_class = AdRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return AdRequest.objects.filter(advertiser=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(advertiser=self.request.user)


class AdAnalyticsView(viewsets.ViewSet):
    """Analytics and reporting for ads"""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get dashboard metrics"""
        campaigns = AdCampaign.objects.filter(advertiser=request.user)
        
        total_metrics = campaigns.aggregate(
            total_impressions=Sum('impressions'),
            total_clicks=Sum('clicks'),
            total_conversions=Sum('conversions'),
            total_spent=Sum('spent'),
            total_budget=Sum('budget'),
        )
        
        return Response({
            'total_campaigns': campaigns.count(),
            'active_campaigns': campaigns.filter(status='active').count(),
            'metrics': total_metrics,
            'average_ctr': self._calculate_average_ctr(total_metrics),
        })
    
    @staticmethod
    def _calculate_average_ctr(metrics):
        impressions = metrics.get('total_impressions') or 0
        clicks = metrics.get('total_clicks') or 0
        return round((clicks / impressions * 100), 2) if impressions > 0 else 0
