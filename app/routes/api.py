from flask import Blueprint, jsonify
from app.models.models import Province, District, Ward, Rule, AmenityCategory, Amenity

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/provinces', methods=['GET'])
def get_provinces():
    """Lấy danh sách tất cả tỉnh/thành phố"""
    try:
        provinces = Province.query.filter_by(is_active=True).all()
        return jsonify({
            'success': True,
            'data': [province.to_dict() for province in provinces]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@api_bp.route('/provinces/<province_code>/districts', methods=['GET'])
def get_districts_by_province(province_code):
    """Lấy danh sách quận/huyện theo tỉnh/thành phố"""
    try:
        province = Province.query.filter_by(code=province_code, is_active=True).first()
        if not province:
            return jsonify({
                'success': False,
                'message': 'Tỉnh/thành phố không tồn tại'
            }), 404
        
        districts = District.query.filter_by(province_id=province.id, is_active=True).all()
        return jsonify({
            'success': True,
            'data': [district.to_dict() for district in districts]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@api_bp.route('/districts/<district_code>/wards', methods=['GET'])
def get_wards_by_district(district_code):
    """Lấy danh sách phường/xã theo quận/huyện"""
    try:
        district = District.query.filter_by(code=district_code, is_active=True).first()
        if not district:
            return jsonify({
                'success': False,
                'message': 'Quận/huyện không tồn tại'
            }), 404
        
        wards = Ward.query.filter_by(district_id=district.id, is_active=True).all()
        return jsonify({
            'success': True,
            'data': [ward.to_dict() for ward in wards]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# API để lấy tất cả dữ liệu cùng lúc (để cache)
@api_bp.route('/locations/all', methods=['GET'])
def get_all_locations():
    """Lấy tất cả dữ liệu địa chỉ để cache trên client"""
    try:
        provinces = Province.query.filter_by(is_active=True).all()
        result = {}
        
        for province in provinces:
            districts_data = {}
            for district in province.districts:
                if district.is_active:
                    wards_data = [ward.name for ward in district.wards if ward.is_active]
                    districts_data[district.code] = {
                        'name': district.name,
                        'wards': wards_data
                    }
            
            result[province.code] = {
                'name': province.name,
                'districts': districts_data
            }
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ================================
# Rules API Endpoints
# ================================

@api_bp.route('/rules', methods=['GET'])
def get_all_rules():
    """Lấy danh sách tất cả nội quy"""
    try:
        rules = Rule.query.filter_by(is_active=True).all()
        
        # Nhóm rules theo category
        rules_by_category = {}
        for rule in rules:
            category = rule.category
            if category not in rules_by_category:
                rules_by_category[category] = []
            rules_by_category[category].append(rule.to_dict())
        
        return jsonify({
            'success': True,
            'data': rules_by_category
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@api_bp.route('/rules/category/<category>', methods=['GET'])
def get_rules_by_category(category):
    """Lấy danh sách nội quy theo category"""
    try:
        rules = Rule.query.filter_by(category=category, is_active=True).all()
        return jsonify({
            'success': True,
            'data': [rule.to_dict() for rule in rules]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ================================
# Amenities API Endpoints
# ================================

@api_bp.route('/amenities', methods=['GET'])
def get_all_amenities():
    """Lấy danh sách tất cả tiện nghi theo categories"""
    try:
        categories = AmenityCategory.query.filter_by(is_active=True).order_by(AmenityCategory.display_order).all()
        
        result = {}
        for category in categories:
            amenities = Amenity.query.filter_by(
                category_id=category.id, 
                is_active=True
            ).order_by(Amenity.display_order).all()
            
            result[category.code] = {
                'category_info': category.to_dict(),
                'amenities': [amenity.to_dict() for amenity in amenities]
            }
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@api_bp.route('/amenities/categories', methods=['GET'])
def get_amenity_categories():
    """Lấy danh sách các loại tiện nghi"""
    try:
        categories = AmenityCategory.query.filter_by(is_active=True).order_by(AmenityCategory.display_order).all()
        return jsonify({
            'success': True,
            'data': [category.to_dict() for category in categories]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@api_bp.route('/amenities/category/<category_code>', methods=['GET'])
def get_amenities_by_category(category_code):
    """Lấy danh sách tiện nghi theo loại"""
    try:
        category = AmenityCategory.query.filter_by(code=category_code, is_active=True).first()
        if not category:
            return jsonify({
                'success': False,
                'message': 'Loại tiện nghi không tồn tại'
            }), 404
        
        amenities = Amenity.query.filter_by(
            category_id=category.id, 
            is_active=True
        ).order_by(Amenity.display_order).all()
        
        return jsonify({
            'success': True,
            'data': {
                'category': category.to_dict(),
                'amenities': [amenity.to_dict() for amenity in amenities]
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500