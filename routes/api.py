from flask import Blueprint, jsonify
from models import Province, District, Ward

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